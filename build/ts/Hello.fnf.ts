let cx : any = {};

class Colour {
    red : number = 0;
    green: number = 0;
    blue: number = 0;
}
class _Hello {
my_colour : Colour = new Colour(1, 2, 3);
hello() : number {
    cx.print("hey what's up");
    return 0;
}
print(... args: string[]) : void {
    console.log(...args);
}
}

cx["print"] = _Hello.prototype.print;
cx.print("hey what's up");