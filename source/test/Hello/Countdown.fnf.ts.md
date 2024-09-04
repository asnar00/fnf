ᕦ(ツ)ᕤ
# Countdown

This is a whole new feature we're adding to the original `Hello` program!

    feature Countdown extends Hello {

We declare a new function to count down from 10:

    on countdown() {
        for(let i=10; i > 0; i--) {
            output(`${i}`);
            wait(100);
        }
    }

And plug it in so it runs whenever `hello()` is called, before the existing definition:

    on hello(name: string): number {
        countdown();
    }

Finally, let's define the `wait()` function:

    on wait(msec: number) : Promise<void> {
        return new Promise(resolve => setTimeout(resolve, msec));
    }
