ᕦ(ツ)ᕤ
# Countdown

This is a whole new feature we're adding to the original `Hello` program!

    feature Countdown extends Hello {

We declare a new function to count down from 10:

```ts
    on countdown() {
        for(let i=10; i > 0; i--) {
            output(`${i}`);
            wait(100)
        }
    }
```

And plug it in so it runs whenever `hello()` is called, before the existing definition:

```ts
on hello(name: string): number {
    countdown(); 
    return _result;
}
```

Finally, let's define the sleep() function:

```ts
on wait(msec: number) : Promise<void> {
    return new Promise(resolve => setTimeout(resolve, msec));
}
```