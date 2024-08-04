ᕦ(ツ)ᕤ
# Hello

This is a small program expressed in *feature normal typescript* that prints "hello world" to the console.

    feature Hello

And here's the function that does the work; we're returning a number just to show how the code looks.

    def hello() : number {
        print("hey what's up");
        return 0;
    }

The `def` keyword means that we're defining a new function called `hello`; if there's already one defined with that name, we get an error.

We define our own function `print` that initially outputs to standard console, but eventually can also print stuff in the browser, or anywhere else we like. That's the magic of features!

```ts
def print (msg: string, indent: number=0) {
    console.log(msg);
}
```

Let's define a little structure as well:

    struct Colour {
        red : number = 0;
        green: number = 0;
        blue: number = 0;
    }

And we can also define feature-scoped variables like this:

    my_colour : Colour = new Colour(1, 2, 3);

We can run this and get the console live in the code viewer (eventually) using this lovely formulation:

    hello() ==> 

And we can also test the result against a known-good value:

    hello() ==> 0

