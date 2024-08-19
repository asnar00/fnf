ᕦ(ツ)ᕤ
# Countdown

This is a whole new feature we're adding to the original `Hello` program!

    feature Countdown extends Hello {

We declare a new function to count down from 10:

    on countdown() {
        output("10 9 8 7 6 5 4 3 2 1")
    }

And plug it in so it runs whenever `hello()` is called, after the existing definition:

    before hello(name: string): number {
        countdown();
    }