ᕦ(ツ)ᕤ
# Hello

This is a small program expressed in *feature normal typescript* that prints "hello world" to the console.

```ts
feature Hello extends Feature {
```

And here's the function that does the work; we're returning a number just to show how the code looks.

```ts
on hello(name: string) : number {
    output(`hello, ${name}!`);
    return 42;
}
```

The `on` keyword means that we're defining a new function called `hello`.

We define our own function `output` that initially outputs to standard console. Later, we'll look at getting this same function to output to the browser.

```ts
on output(msg: string, indent: number=0) {
    console.log(" ".repeat(indent) + msg);
}
```

Let's define a little structure as well:

```ts
struct Colour { 
    red : number = 0; 
    green: number = 0; 
    blue: number = 0; 
}
```

And we can also define feature-scoped variables like this:

```ts
local my_colour : Colour = new Colour(1, 2, 3);
```

We can run this and get the console live in the code viewer (eventually) using this lovely formulation:

```ts
> hello("world") ==> 42
```

And we can also test the result against a known-correct value:

```ts
> let x: number = 1;
> my_colour.red ==> x
```

Finally, we'll declare a `main` function that calls `hello`:

    replace main() {
        hello("world");
    }