import winsound
import time

# Diccionario de código morse
morse_dict = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.',
    'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.',
    'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-',
    'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..',
    '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', '6': '-....',
    '7': '--...', '8': '---..', '9': '----.', '0': '-----', ' ': '/'
}

# Función para reproducir el sonido del código Morse
def play_morse(morse_code):
    dot_duration = 200  # duración del punto en milisegundos
    dash_duration = dot_duration * 3  # duración del guion
    frequency = 1000  # frecuencia del sonido en Hz

    for symbol in morse_code:
        if symbol == '.':
            winsound.Beep(frequency, dot_duration)
        elif symbol == '-':
            winsound.Beep(frequency, dash_duration)
        elif symbol == ' ':
            time.sleep(dot_duration / 1000)  # Pequeña pausa entre letras
        time.sleep(dot_duration / 1000)  # Pausa entre símbolos

# Función para convertir texto a código Morse
def text_to_morse(text):
    morse_code = ""
    for char in text.upper():
        morse_code += morse_dict.get(char, '') + ' '
    return morse_code.strip()

# Ejemplo de uso
texto = input("Ingresa el texto a convertir: ")
codigo_morse = text_to_morse(texto)
print(f"Texto en morse: {codigo_morse}")
play_morse(codigo_morse)
