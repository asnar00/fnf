ᕦ(ツ)ᕤ

# Hello

This is a small program expressed in _feature normal C++_ that prints "hello world" to the console.

```cpp
feature Hello extends Feature {
```

And here's the function that does the work; we're returning a number just to show how the code looks.

```cpp
def number hello(string name) {
    output("hey what's up {name}");
    return 42;
}
```

The `def` keyword means that we're defining a new function called `hello`; if there's already one defined with that name, we get an error.

We define our own function `output` that initially outputs to standard console, but eventually can also print stuff in the browser, or anywhere else we like. That's the magic of features!

```cpp
def output(string msg, int indent =0) {
    cout << msg;
}
```

Let's define a little structure as well:

```cpp
struct Colour { 
    int red = 0; 
    int green = 0; 
    int blue = 0;
}
```

And we can also define feature-scoped variables like this:

```cpp
Colour my_colour = Colour(1, 2, 3);
```

We can run this and get the console live in the code viewer (eventually) using this lovely formulation:

```cpp
> hello() ==> 
```

And we can also test the result against a known-correct value:

```cpp
> hello() ==> 42
```