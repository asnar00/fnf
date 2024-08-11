ᕦ(ツ)ᕤ
# Hello

This is a small program expressed in *feature normal python* that prints "hello world" to the console.

    feature Hello extends Feature:

And here's the function that does the work; we're returning a number just to show how the code looks.

    def hello(name: string) -> int:
        output("hey what's up {name}")
        return 42

The `def` keyword means that we're defining a new function called `hello`; if there's already one defined with that name, we get an error.

We define our own function `output` that initially outputs to standard console, but eventually can also print stuff in the browser, or anywhere else we like. That's the magic of features!

```py
def output(msg: string, indent: number=0):
    print(msg)
```

Let's define a little structure as well:

    struct Colour:
        red : number = 0
        green: number = 0
        blue: number = 0
    

And we can also define feature-scoped variables like this:

    my_colour : Colour = Colour(1, 2, 3)

We can run this and get the console live in the code viewer (eventually) using this lovely formulation:

    hello() ==> 

And we can also test the result against a known-correct value:

    hello() ==> 42


