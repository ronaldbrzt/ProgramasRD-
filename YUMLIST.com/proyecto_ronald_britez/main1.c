#include <stdio.h>
#include <unistd.h> // Para usar sleep/usleep

void pantalla_carga() {
    int i;
    printf("\nCalculando");
    for (i = 0; i <= 100; i += 5) {
        printf("\rCalculando: %d%%", i);
        fflush(stdout); // Forzar salida inmediata
        usleep(50000);  // 50 ms = 0.05 segundos, puedes ajustar la velocidad
    }
    printf("\n");
}

int main() {
    float num1, num2, resultado;
    char operacion;

    printf("Calculadora básica en C\n");
    printf("Introduce el primer número: ");
    scanf("%f", &num1);

    printf("Introduce la operación (+, -, *, /): ");
    scanf(" %c", &operacion);

    printf("Introduce el segundo número: ");
    scanf("%f", &num2);

    pantalla_carga();

    switch (operacion) {
        case '+':
            resultado = num1 + num2;
            printf("Resultado: %.2f\n", resultado);
            break;
        case '-':
            resultado = num1 - num2;
            printf("Resultado: %.2f\n", resultado);
            break;
        case '*':
            resultado = num1 * num2;
            printf("Resultado: %.2f\n", resultado);
            break;
        case '/':
            if (num2 != 0) {
                resultado = num1 / num2;
                printf("Resultado: %.2f\n", resultado);
            } else {
                printf("Error: División por cero\n");
            }
            break;
        default:
            printf("Operación no válida\n");
    }

    return 0;
}
