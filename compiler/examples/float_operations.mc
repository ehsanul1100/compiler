// Float operations
float celsius_to_fahrenheit(float celsius) {
    return celsius * 9.0 / 5.0 + 32.0;
}

float fahrenheit_to_celsius(float fahrenheit) {
    return (fahrenheit - 32.0) * 5.0 / 9.0;
}

float temp_c = 25.0;
float temp_f = celsius_to_fahrenheit(temp_c);
print(temp_f);

float back_to_c = fahrenheit_to_celsius(temp_f);
print(back_to_c);