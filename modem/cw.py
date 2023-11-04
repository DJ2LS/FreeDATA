import numpy as np

"""
 morse code generator
 MorseCodePlayer().text_to_signal("DJ2LS-1")

 
 """


class MorseCodePlayer:
    def __init__(self, wpm=25, f=1500, fs=48000):
        self.wpm = wpm
        self.f0 = f
        self.fs = fs
        self.dot_duration = 1.2/(self.wpm)
        self.dash_duration = 3*self.dot_duration
        self.pause_duration = self.dot_duration
        self.word_pause_duration = 7*self.dot_duration
        self.morse_alphabet = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
            'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
            'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
            '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--',
            '?': '..--..', "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...',
            ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-', '_': '..--.-', '"': '.-..-.',
            '$': '...-..-', '@': '.--.-.'
        }

    def text_to_morse(self, text):
        morse = ''
        for char in text:
            if char.upper() in self.morse_alphabet:
                morse += self.morse_alphabet[char.upper()] + ' '
            elif char == ' ':
                morse += ' '
        return morse

    def morse_to_signal(self, morse):
        signal = np.array([], dtype=np.int16)
        for char in morse:
            if char == '.':
                duration = self.dot_duration  # Using class-defined duration
                t = np.linspace(0, duration, int(self.fs * duration), endpoint=False)
                s = 0.5 * np.sin(2 * np.pi * self.f0 * t)
                signal = np.concatenate((signal, np.int16(s * 32767)))
                pause_samples = int(self.pause_duration * self.fs)
                signal = np.concatenate((signal, np.zeros(pause_samples, dtype=np.int16)))

            elif char == '-':
                duration = self.dash_duration  # Using class-defined duration
                t = np.linspace(0, duration, int(self.fs * duration), endpoint=False)
                s = 0.5 * np.sin(2 * np.pi * self.f0 * t)
                signal = np.concatenate((signal, np.int16(s * 32767)))
                pause_samples = int(self.pause_duration * self.fs)
                signal = np.concatenate((signal, np.zeros(pause_samples, dtype=np.int16)))

            elif char == ' ':
                pause_samples = int(self.word_pause_duration * self.fs)
                signal = np.concatenate((signal, np.zeros(pause_samples, dtype=np.int16)))
                pause_samples = int(self.pause_duration * self.fs)
                signal = np.concatenate((signal, np.zeros(pause_samples, dtype=np.int16)))

        return signal

    def text_to_signal(self, text):
        morse = self.text_to_morse(text)
        return self.morse_to_signal(morse)

