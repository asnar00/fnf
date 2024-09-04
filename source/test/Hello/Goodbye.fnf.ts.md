ᕦ(ツ)ᕤ
# Goodbye

This is a whole new feature we're adding to the original `Hello` program!

    feature Goodbye extends Hello {

We declare a new function to say goodbye:

    on goodbye() {
        output("kthxbai.");
    }

And plug it in so it runs whenever `hello()` is called, after the existing definition:

    after hello(name: string): number {
        goodbye();
        return _result + 1;
    }
