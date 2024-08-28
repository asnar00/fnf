// ᕦ(ツ)ᕤ
// generated by fnf.py

// ----------------------------------------------------------------
// logging functions

var _file = "";
function _output(value: any, loc: string) { console.log(`${loc}:OUTPUT: ${value}`); }
function _assert(lhs: any, rhs: any, loc: string) { if (lhs !== rhs) console.log(`${loc}:FAIL: ${lhs}`); else console.log(`${loc}:PASS`); }

// ----------------------------------------------------------------
// context

namespace mycontext {
    class Colour {
        red: number =  0;
        green: number =  0;
        blue: number =  0;
        constructor(red: number =  0, green: number =  0, blue: number =  0) {
            this.red = red;
            this.green = green;
            this.blue = blue;
        }
    }
    var my_colour : Colour =  new Colour(1, 2, 3);
    export async function hello(name: string) : Promise<number|undefined> {
        var _result: number|undefined;
        _result = await (async () => {
            const results = await Promise.all([
                (() => {
                    // ------------------------ Hello ------------------------
                    _result = (() => {
                        output(`hello, ${name}!`);
                        return 42;
                    })();
                    // ------------------------ Goodbye ------------------------
                    _result = (() => {
                        goodbye();
                        return _result + 1;
                    })();
                    return _result;
                })()
                ,
                // ------------------------ Countdown ------------------------
                (async () => {
                    (await countdown());
                })()
            ]);
            const validResults = results.filter(result => result !== undefined);
            return validResults.length > 0 ? validResults[0] : undefined;
        })();
        return _result;
    }
    export function output(msg: string, indent: number = 0) {
        var _result: undefined;
        // ------------------------ Hello ------------------------
        (() => {
            console.log(" ".repeat(indent) + msg);
        })();
    }
    export async function main() : Promise<void|undefined> {
        var _result: undefined;
        // ------------------------ Hello ------------------------
        await (async () => {
            (await hello("world"));
        })();
    }
    export function goodbye() {
        var _result: undefined;
        // ------------------------ Goodbye ------------------------
        (() => {
            output("kthxbai.");
        })();
    }
    export async function countdown() : Promise<void|undefined> {
        var _result: undefined;
        // ------------------------ Countdown ------------------------
        await (async () => {
            for(let i=10; i > 0; i--) {
                output(`${i}`);
                (await wait(100));
            }
        })();
    }
    export async function wait(msec: number) : Promise<void> {
        var _result: void|undefined;
        // ------------------------ Countdown ------------------------
        _result = await (async () => {
            return new Promise(resolve => setTimeout(resolve, msec));
        })();
        return _result;
    }
    export async function _test() {
        const _Hello_test = async () => {
            _assert((await hello("world")), 42, "source/fnf/Hello.fnf.ts.md:39:2");
            let x: number = 1;
            _assert(my_colour.red, x, "source/fnf/Hello.fnf.ts.md:44:2");
        };
        const _Goodbye_test = () => {
        };
        const _Countdown_test = () => {
        };
        try { await _Hello_test(); } catch (e) { console.error(e); }
        try { _Goodbye_test(); } catch (e) { console.error(e); }
        try { _Countdown_test(); } catch (e) { console.error(e); }
    }
}

// ----------------------------------------------------------------
// entry point

async function main() {
    if (Deno.args.indexOf("-test") >= 0) {
        console.log("testing mycontext...");
        await mycontext._test();
        return;
    }
}

main();
