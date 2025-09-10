// Boolean logic example
bool isEven(int n) {
    return n % 2 == 0;
}

for (int i = 1; i <= 10; i = i + 1) {
    bool even = isEven(i);
    if (even) {
        print(i);
    }
}