import numpy as np

"""
 morse code generator
 MorseCodePlayer().text_to_signal("DJ2LS-1")

 
 """


class MorseCodePlayer:
    """Generates and plays morse code audio.

    This class provides functionality to convert text to morse code and then
    to an audio signal, allowing for the generation and playback of morse
    code. It supports customization of the code speed (WPM), tone frequency,
    and sampling rate.
    """

    def __init__(self, wpm=25, f=1500, fs=48000):
        """Initializes the MorseCodePlayer.

        Args:
            wpm (int, optional): Words per minute, defining the speed of the morse code. Defaults to 25.
            f (int, optional): Tone frequency in Hz. Defaults to 1500.
            fs (int, optional): Sampling rate in Hz. Defaults to 48000.
        """
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
        """Converts text to morse code.

        This method takes a string of text as input and converts it to morse
        code, using the defined morse alphabet. It handles spaces and
        non-alphanumeric characters.

        Args:
            text (str): The text to convert.

        Returns:
            str: The morse code representation of the input text.
        """
        morse = ''
        for char in text:
            if char.upper() in self.morse_alphabet:
                morse += self.morse_alphabet[char.upper()] + ' '
            elif char == ' ':
                morse += ' '
        return morse

    def morse_to_signal(self, morse):
        """Converts morse code to an audio signal.

        This method takes a string of morse code as input and generates a
        corresponding audio signal. Dots and dashes are represented by sine
        waves of appropriate durations, and pauses are represented by
        silence.

        Args:
            morse (str): The morse code string to convert.

        Returns:
            numpy.ndarray: The generated audio signal.
        """
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
        """Converts text to a morse code audio signal.

        This method takes text as input, converts it to morse code using the
        `text_to_morse` method, and then converts the morse code to an audio
        signal using the `morse_to_signal` method.

        Args:
            text (str): The text to convert to an audio signal.

        Returns:
            numpy.ndarray: The generated audio signal as a NumPy array.
        """
        morse = self.text_to_morse(text)
        return self.morse_to_signal(morse)

