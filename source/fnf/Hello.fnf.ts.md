ᕦ(ツ)ᕤ
# Hello

This is a small program expressed in *feature normal typescript* that prints "hello world" to the console.

    feature Hello extends Feature {

And here's the function that does the work; we're returning a number just to show how the code looks.


    on hello(name: string) : number {
        output(`hello, ${name}!`);
        return 42;
    }


The `on` keyword means that we're defining a new function called `hello`.

We define our own function `output` that initially outputs to standard console. Later, we'll look at getting this same function to output to the browser.


    on output(msg: string, indent: number=0) {
        console.log(" ".repeat(indent) + msg);
    }


Let's define a little structure as well:

    struct Colour { 
        red : number = 0; 
        green: number = 0; 
        blue: number = 0; 
    }

And we can also define feature-scoped variables like this:

    local my_colour : Colour = new Colour(1, 2, 3);

We can run this and get the console live in the code viewer (eventually) using this lovely formulation:

    > hello("world") ==> 42

And we can also test the result against a known-correct value:

    > let x: number = 1;
    > my_colour.red ==> x

Finally, we'll declare a `main` function that calls `hello`:

    replace main() {
        hello("world");
    }