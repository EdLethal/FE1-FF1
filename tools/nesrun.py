"""Frontend minimo de libretro para rodar ROMs de NES sem tela (headless).

Uso:
    import sys; sys.path.insert(0, "/caminho/da/pasta/tools")
    from nesrun import Emu
    e = Emu("/caminho/fceumm_libretro.so", "/caminho/jogo.nes")
    e.run(60)                  # avanca 60 quadros
    e.tap("start")             # aperta e solta START
    e.screenshot("a.png")      # salva a tela (escala opcional)
    e.ram(0x0010, 4)           # le RAM interna ($0000-$07FF)
    e.sram(0x6000, 16)         # le a RAM de save/bateria ($6000-$7FFF)
"""
import ctypes as C

import numpy as np
from PIL import Image

BUTTONS = {"b": 0, "y": 1, "select": 2, "start": 3, "up": 4, "down": 5,
           "left": 6, "right": 7, "a": 8, "x": 9, "l": 10, "r": 11}

ENV_FN = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO_FN = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO_FN = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDIO_BATCH_FN = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL_FN = C.CFUNCTYPE(None)
STATE_FN = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)


class GameInfo(C.Structure):
    _fields_ = [("path", C.c_char_p), ("data", C.c_void_p),
                ("size", C.c_size_t), ("meta", C.c_char_p)]


class Emu:
    def __init__(self, core_path, rom_path):
        self.lib = C.CDLL(core_path)
        self.pixel_format = 1  # 0=0RGB1555 1=XRGB8888 2=RGB565
        self.frame = None
        self.held = set()
        self.frames_run = 0
        self._dir = C.c_char_p(b".")

        def env(cmd, data):
            if cmd == 10 and data:      # SET_PIXEL_FORMAT
                self.pixel_format = C.cast(data, C.POINTER(C.c_int))[0]
                return True
            if cmd == 3 and data:       # GET_CAN_DUPE
                C.cast(data, C.POINTER(C.c_bool))[0] = True
                return True
            if cmd in (9, 31) and data:  # GET_SYSTEM_DIRECTORY / GET_SAVE_DIRECTORY
                C.cast(data, C.POINTER(C.c_char_p))[0] = self._dir.value
                return True
            if cmd in (11, 16):         # SET_INPUT_DESCRIPTORS / SET_VARIABLES
                return True
            return False

        def video(data, w, h, pitch):
            if not data:
                return
            raw = C.string_at(data, pitch * h)
            if self.pixel_format == 1:
                a = np.frombuffer(raw, np.uint8).reshape(h, pitch)[:, : w * 4].reshape(h, w, 4)
                self.frame = a[:, :, [2, 1, 0]].copy()
            elif self.pixel_format == 2:
                a = np.frombuffer(raw, np.uint16).reshape(h, pitch // 2)[:, :w]
                r, g, b = (a >> 11) & 31, (a >> 5) & 63, a & 31
                self.frame = np.stack([r * 255 // 31, g * 255 // 63, b * 255 // 31], -1).astype(np.uint8)
            else:
                a = np.frombuffer(raw, np.uint16).reshape(h, pitch // 2)[:, :w]
                r, g, b = (a >> 10) & 31, (a >> 5) & 31, a & 31
                self.frame = np.stack([r * 255 // 31, g * 255 // 31, b * 255 // 31], -1).astype(np.uint8)

        def state(port, device, index, bid):
            if port == 0 and device == 1 and bid in self.held:
                return 1
            return 0

        self._cbs = (ENV_FN(env), VIDEO_FN(video), AUDIO_FN(lambda l, r: None),
                     AUDIO_BATCH_FN(lambda d, n: n), POLL_FN(lambda: None), STATE_FN(state))
        L = self.lib
        L.retro_set_environment(self._cbs[0])
        L.retro_init()
        L.retro_set_video_refresh(self._cbs[1])
        L.retro_set_audio_sample(self._cbs[2])
        L.retro_set_audio_sample_batch(self._cbs[3])
        L.retro_set_input_poll(self._cbs[4])
        L.retro_set_input_state(self._cbs[5])
        L.retro_get_memory_data.restype = C.c_void_p
        L.retro_get_memory_data.argtypes = [C.c_uint]
        L.retro_get_memory_size.restype = C.c_size_t
        L.retro_get_memory_size.argtypes = [C.c_uint]

        with open(rom_path, "rb") as f:
            self._rom = C.create_string_buffer(f.read())
        info = GameInfo(rom_path.encode(), C.cast(self._rom, C.c_void_p), len(self._rom.raw), None)
        if not L.retro_load_game(C.byref(info)):
            raise RuntimeError("o core recusou a ROM")
        L.retro_set_controller_port_device(0, 1)

    def run(self, frames=1):
        for _ in range(frames):
            self.lib.retro_run()
            self.frames_run += 1

    def hold(self, *buttons):
        self.held = {BUTTONS[b] for b in buttons}

    def tap(self, button, hold=4, wait=12):
        self.hold(button)
        self.run(hold)
        self.hold()
        self.run(wait)

    def screenshot(self, path, scale=1):
        img = Image.fromarray(self.frame)
        if scale != 1:
            img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        img.save(path)
        return img

    def _mem(self, mem_id, base, addr, n):
        ptr = self.lib.retro_get_memory_data(mem_id)
        size = self.lib.retro_get_memory_size(mem_id)
        off = addr - base
        if not ptr or off < 0 or off + n > size:
            raise ValueError(f"memoria {mem_id} indisponivel (tamanho {size})")
        return C.string_at(ptr + off, n)

    def ram(self, addr, n=1):
        return self._mem(2, 0x0000, addr, n)

    def sram(self, addr, n=1):
        return self._mem(0, 0x6000, addr, n)
