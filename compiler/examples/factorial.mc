// Control flow example with loops
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

for (int i = 1; i <= 5; i = i + 1) {
    int fact = factorial(i);
    print(fact);
}