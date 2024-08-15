ᕦ(ツ)ᕤ
# Hello

This is a small program expressed in _feature normal typescript_ that prints "hello world" to the console.

```ts
feature Goodbye extends Hello {
```

All it does it output "bye!" after `Hello` runs. This is how we do it:

First, we define a new function called `goodbye()` that outputs "bye":

```ts
on goodbye() {
    output("bye!")
}
```
And then we "plug it in" to the existing program by extending the existing `hello` function; we just bolt on a call to `goodbye` whenever `hello` is called. The syntax is like this:

```ts
after hello(name: string) : number { 
    goodbye();
    return _result + 1;
}
```


