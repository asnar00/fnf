class Colour {
    red : number = 0;
    green : number = 0;
    blue : number = 0;
    constructor(red : number = 0, green : number = 0, blue : number = 0) {
        this.red = red;
        this.green = green;
        this.blue = blue;
    }
}

class _Hello extends _Feature {
    my_colour : Colour = new Colour(1, 2, 3);
    
    static hello(_cx: any) : number {
        _cx.print(_cx, "hey what's up");
        return 0;
    }
    static print(_cx: any, msg : string, indent : number = 0) : void {
        console.log(msg);
    }
}
