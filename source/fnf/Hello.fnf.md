ᕦ(ツ)ᕤ
# Hello

This is a small program expressed in *feature normal typescript* that prints "hello world" to the console.

    feature Hello;

And here's the function that does the work.

    def hello() : number {
        print("hey what's up");
        return 0;
    }

We define our own function `print` that initially outputs to standard console, but eventually can also print stuff in the browser. That's the magic of features!

```ts
def print (... args: string[]) {
    console.log(...args);
}
```

Let's define a little structure as well:

    struct Colour {
        static name : number = 0;
        green: number = 0;
        blue: number = 0;
    }

We can run this and get the console live in the code viewer (eventually) using this lovely formulation:

    hello() ===> 

