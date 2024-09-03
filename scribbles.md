ᕦ(ツ)ᕤ
# scribbles

The objection to "feature modular anything" is that it's too complex, and I'm not really sure what the objective is.

I prefer "zero with agnostic syntax and multiple backends" - which is a proper language with code generation coming out the wazoo. I want to build that in something that's performant and cross-platform.

Maybe zig is fun to try?

---------------------------------------------------------------------

new rules:
- start fresh every morning
- don't think about what others may want
- just do what seems most fun

this means right now:

- just do everything in one file
- just try stuff out

-------------------------------------------------------------------------
Get current fm.ts functionality working with new parser structure.
Then: holiday time!
- VR coding: hello cube
- vault: serve files based on eyescan stuff
- local llama 3.1 experiments
- le website

-----------------------------------------------------------------
OK 40000 foot view again here: what's the right steer once the parser's upgraded?
I'd say with a bit more of a push tomorrow I can get it where I need it by the weekend:
passing the same tests. => we could go down the lexer route but I think that's unnecessary.

There's some stuff to do with capturing the whitespace / lines *around* matches, somehow, so the layout gets preserved along with the other stuff. Like, when we skipWhitespace, we somehow record the resulting thing in the AST. Is that weird? 

_________________________________________
State of play:
we've demonstrated the full range of parser/printer elements:
keyword, identifier, sequence, list, anyof, enum, etc.

Next step: do parse/print tests for typescript.
Then: do the function-builder by manipulating the AST, then output in target language.
That's next!

OK no: the right way forward is:

- return to typescript output parity
- implement python workflow

Then rebuild the whole system in FNF, from the ground up.

What if that was the "big deal", we impose a syntax on you, but it "gives" in all the right places.

So there's some basic things like `type name` vs `name: type` and so on. And we can actually generate output code. So we're not just fucking about.

This way, we have a sort of "flexible" syntax that accommodates you whether you come from C*, python, or whatever - but it's as opinionated as zero is, and has a multi-backend builder thingy that just fucking works. OK, that's actually a super nice next thing to do.

So there's three syntax forms: cxx, python, typescript. Which takes care of the main incoming contingent. Code looks like you're used to, and it just works.

So can we do this? Like a "flexible" system? Hm seems cool. A much better way of doing it because then you can write the code in zero, huhuhuhuhuh.

ok that's the way forward.

------------------------------------

=> just fucking do it.

OK so this was a great week and lots of shit got done.
BIG learning was "I finally get parsers"

The next obvious thing is to be able to directly manipulate AST entities (functions/features/etc) and have the backend spit out the right code.

To do this, we need a new parser framework.

===>

So let's think about how the same interface (calling parser functions) can also be used to *print* things out.

Let's take a really simple, one the feature declaration. Let's also modify the "Source" class to be able to print stuff to the file, including things that contain sources! This lets us handle source mapping without really thinking about it too much.

    sequence(keyword("feature"), 
                    set("name", word()),
                    optional(sequence(keyword("extends"), set("parent", word()))))

So let's think about how this might actually play out with print.
We'd parse this and get an AST node: a dictionary like this:

    { "_type": "feature", "name": "MyFeature", "parent", "AnotherFeature" }

"MyFeature" and "AnotherFeature" are not strings, they're actually Source instances pointing into the original code, but we'll skip over this detail for now.

So let's start from the outside:

    print_sequence(ast, out, *printerFns):
        pos = out.start
        for printerFn in printerFns:
            if printerFn(ast, out)==False:
                out.reset(pos)
                return False
        return True

    print_set(ast, out, varname, printerFn):
        if varname in ast:
            return printerFn(ast[varname], out)
        else: 
            return False

    print_optional(ast, out, printerFn):
        pos = out.start
        if printerFn(ast, out): 
            return True
        else:
            out.start = pos
            return False

    print_keyword(ast, out, val):
        out.print(val)
        return True

    print_word(ast, out):
        if isinstance(ast, Source):
            out.print(ast)
            return True
        else:
            return False

So what should happen here is:

    print_sequence(
        print_keyword               => "feature"
        print_set
            print_word              => "MyFeature" [including sourcemap]
        optional
            print_sequence
                print_keyword       => "extends"
                print_set           succeeds
                    print_word      => "AnotherFeature"

So if we don't have "extends", then print_set will fail, print_sequence will fail, and optional will reset.

The key thing is the signature.

Given

    fn(args)

There's:

    parse_fn(in, args) -> ast

and

    print_fn(ast, out, args) -> bool

When we want to parse, we'll do 

    ast = generate_parser(fn)(in)

When we want to print, we'll do 

    generate_printer(fn)(ast, out)

So there's something that fn(args) has to return, and it's either:

    lambda x : parse_fn(x, args)

OR

    lambda x y : print_fn(x, y, args)

So what if it returns a function that can call either of those?

    def fn(*args):
        return lambda b x y : if b: parse_fn(x, args) else print_fn(x, y, args)

and then you just either call

    fn(True, source, None)      to parse

or

    fn(False, ast, source)      to print

et voila. A little convoluted. You could do it like:

    def fn(*args):
        return lambda obj x y obj.fn(x, y, *args)

and then you have parser, printer, whatever. That's the right way.

OK so the next thing is we implement this, and it passes the async test, but the code is nicer.





----------------------------------------------------
DONE! on-async now works as intended. 
The code in typescript is super gnarly.
Needs a total refactor so that we can use the parser mechanism.
Ultimately we need to be doing this computation at a higher level,
and each language module takes care *only* of outputting high-level structures.

---------------------------------------------------

Okay, so we're now computing the async status of output functions thusly:

- if a stub contains "await", returns a promise, or is "async" declared
- if a stub calls another async function

we're storing fine-grained stub status as func["async"], and also holding a dictionary of name=>async.

Also same for tests.

Behaves correctly wrt timing: countdown waits one second per number.
Still need to implement `on` concurrency, that's the next job.
Also tests wait for the whole console including timing, and all console lines pop out at the same time.
Which isn't great, but it's fine for the moment. We'll do something more complex that reads console outputs line by line.

so that's our to-do list for tomorrow:

1. line-by-line pickup of test output
2. `on` concurrency
3. `main` function so we can actually run things. Auto-re-run would be nice.



-----------------------------------------

So let's think about on, async, time, and that kind of thing.

Given that previous work is pushing us to named-result and streams-instead-of-side-effects, let's just explore what this might mean.

This is code using `local` to define an output stream:

    // hello.md
    feature Hello {
        local out: string;
        on hello(name: string) {
            out << `hello ${name}!`;
        }
        replace main() { 
            out << hello("asnaroo");
        }
    }

    // goodbye.md
    feature Goodbye extends Hello {
        on goodbye() {
            out << "bye!";
        }
        after hello() {
            goodbye();
        }
    }

    // countdown.md
    feature Countdown extends Hello {
        on countdown() {
            out << "10 9 8 7 6 5 4 3 2 1";
        }
        before hello() {
            countdown();
        }
    }

Let's think about the Colour example:

    // rgb.md
    feature RGB {
        struct Colour {
            red: number = 0;
            green: number = 0;
            blue: number = 0;
        }
        on (r: Colour) = add_colours(a: Colour, b: Colour) {
            r = new Colour(a.red + b.red, a.green + b.green, a.blue + b.blue);
        }
    }

    // alpha.md
    feature Alpha extends RGB {
        struct Colour {
            alpha: number = 1;
        }
        on (r: Colour) = add_colours(a: Colour, b: Colour) {
            r.a = a.alpha + b.alpha;
        }
    }

So what should the output code look like?





-------------------------------------------------------------------------------------

So next step then is (deep breath) concurrency, namely the `on` keyword.

A really simple way of handling all of this is to bifurcate `on` into two forms:

- if it's a void-returning function then just run them async, await both

- if it's a result-returning function, then we need to split the function into two things: 1) the parallel bit and 2) the bit that combines them together. 

    on blah(...): rt {
        result1 = fork(_blah);           // call old code
        result2 = fork(newblah);         // concurrently with new code
        return fn(result1, result2);     // combine the results
    }
    
We'd have to think about this. It would be something like:

- if it's super small, eg. colour alpha, then "on" effectively means "either before or after, don't care"

    on r: Colour = (a: Colour) + (b: Colour) {
        r.a = a.a + b.a;
    }

So here because it's only one line, we wouldn't go all the effort of parallelising the solution. This pattern really works because there's no questions about allocating space for the result - r already exists and has a place somewhere, so we literally don't care about where it is.

I'm actually super super close to making the decision to just go for named-results. It just fucking makes sense.

I think the `Colour` example is the convincing argument for why we need named results. This would then let us do the really nice scope-less code replacement.

So decisions:

1. We're going for the named-result pattern
2. We'll change code-generation to be function-call-less (just scopes)
    => much cleaner, doesn't assume lambdas/closures which I don't like
3. Then we do "on" parallel cases for Colour add and timeout countdown.




--------------------------------------------------------------

With that out of the way, let's think about the next step.
=> we could decide that we'd rather just output super efficient code, but I think that optimisation can wait. Or can it? We want to be performant, after all, otherwise what's the point?

OK, so let's just think for a second about what we'd have to do make this really efficient. Fundamentally, you'd transform all `return x` to `_result = x` and lift each body out into its own scope. Any local variables declared inside the stub functions would be restricted to the scope, so that would work.

    export function hello(name: string) : number {
        var _result: number;
        // ------------------------ Countdown ------------------------
        {
            countdown();
        }
        // ------------------------ Hello ------------------------
        {
            output(`hello, ${name}!`);
            _result = 42;
        }
        // ------------------------ Goodbye ------------------------
        {
            goodbye();
            _result = __result + 1;
        }
        return _result;
    }

The only reason this doesn't work is because of the whole `return` thing. return cuts control flow to the end of the function, but doesn't have the same effect within a scope. If there was code after the return, and we did this transformation `_result=`, then the behaviour would change. So we have to somehow get rid of all code following the `return`, which I think ends up being a bit more gnarly than we need.

This does again tend to push us towards the `named results` pattern, but I want to resist that because it isn't totally general. But it would totally make sense here.

    on (r: number) = hello(name: string) {
    }

    before (r: number) = hello(name: string) {
    }

But I don't like this, because it's pushing the whole "dialect" thing a bit too hard. 

Decision: I'm satisfied that the optimisation is possible later, so let's move forward.

-------------------------------------------------------------
after/before are done.

Here's the output ts code for the classic countdown/hello/goodbye example:

    export function hello(name: string) : number {
        var _result: number;
        // ------------------------ Countdown ------------------------
        _result = (() => {
            countdown();
        })();
        if (_result != undefined) return _result;
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
    }

The aims here were:

- locality: don't have to go somewhere else to understand the code; so no separate definitions of hello_Hello and so on.

- reduce recursion: even if that's elegant conceptually, it's just not efficient

- easy generation: work with a sourceblock called "existing", each new fn-application adds new lines to it, voila. Also, don't have to do any complex rewriting of function bodies or innards, we just copy the body wholesale, and it's fine. Note that this wouldn't be the case if we wanted to turn a function into a local-scope within the outer function.

- the early-out / _result patterns work nicely here : was shown to be useful in the microserver.fm experiment - which will continue once this is "stable-ish".

There's potential here to lift functionality up out of the Language class. But I think python, C++ both support this nicely with lambdas. The "define lambda capturing all other variables from the calling context" pattern just means we don't have to repeatedly pass parameters down into functions - we just read the top-level ones. However there's lots of potential here for confusion if we write to parameters... we wouldn't do that ever would we?? ;-)

All in all, I think a reasonable solution for this round. A better solution would obviously be something that works at the AST level, which is something I'll get my head around later.

----------------------------------------------------

Aside for "on" : I'm going back to on/replace, rather than on/def/replace.

Some possible things to think about next:

- feature composition: on, after, before, replace
- accessing _function from replace
- a more generic intermediate compositional form?
- main() entry point to context
- backend-specific context (wrappers for deno fns)
- working demos/tests for py, cpp, swift?
- web editor for vscode  <== important for takeup
- data-driven parser model [many reasons, mainly extensibility]

What's the most important?

- webeditor in vscode, written in fnf.ts

=> this is a great first step, because it's useful functionality and will benefit from fnf.

For this we'll need to get the client/server demo working.
So our first milestone is:

hello world in the browser.

Let's get on with it.

-----------------------------------

OK, so! We have a working deno backend that successfully runs a single feature, `Hello.fnf.ts.md`. All errors are reported mapped back to the original source location, and it's even ... ghasp ... efficient! We avoid storing multiple copies of source filenames per line by creating an object (`SourcePath`) that contains the filename, and then just pass locations around.

Next: get some more features working: goodbye after hello, ask name before hello. Then we'll look at "on" for parallelism.

-------------------------------

So we could totally store this stuff in markdown but you need a special viewer. Which we do anyway. So a vscode plugin is probably a good idea, but it has to be typescript/web anyway.

--------

code generation with proper source-line mapping works, thanks to separating Source from SourceFile!

        def feature(self):
            return label("feature", 
                      sequence(keyword("feature"), 
                        set("name", word()),
                        optional(sequence(
                            keyword("extends"),
                            set("parent", word()) )),
                        self.indent(),
                        set("components", list(self.component())), 
                        self.undent())
                        )

Think of how you'd do this:

    def keyword(value: str):
        def print_keyword(value: str, out: SourceFile):
            out.push(value)
        return lambda dict, out: print_keyword(value, out)


-------
we need to rethink how the source-map thing works.
I think the best way is to actually capture a Source there.
that way we can access the sourcemap nicely.
ok, let's do that.

-----
composite function building:

Hello.md:

```ts
on hello(name: string) : number {
    output(`hey what's up ${name}`);
    return 42;
}
```

Goodbye.md:

```ts
after hello(name: string) : number { 
    goodbye();
    return _result + 1;
}
```

For which the composite function should be:

```ts
    function hello(name: string) : number {
        var _result: number;
        _result = ((name: string):number => {   // feature "Hello"
            output(...);
            return 42;
        })(name);
        _result = ((name: string) : number => { // feature "Goodbye"
            goodbye();
            return _result + 1;
        })(name);
        return _result;
    }
```

so just write code that does this efficiently... not so hard.

--------------

error reporting is now working! surprisingly smooth.
still needs improvement in the optional bit; 
if we've matched some of the optional bit, then we should report the error.
----

Okay... with a bit of string and glue, I now capture test code as well.
Next is ERROR REPORTING. Quite important.
and then a proper parser debugging scheme. Also important.
Something something decorators again. These keep coming up.
Indent preprocessing for significant-whitespace eg. python.


Side project: use the parser functions to print things out properly.
Can we like process the function chain to print things as well?

    def parse_thingy(params, source) -> dict: ...
    def print_thingy(params, dict) -> source ...

I think it's quite important to maintain the python pathway as well.




------

tests: the real issue is that feature scope extends across the whole piece of code, so there's no "outside" - any code in the feature scope is a test.

So really feature-scope is top-level, and we need to therefore take anything that doesn't pass the "component" test and funnel it to the test function.

And this can include all kinds of code that might look like var-decl.

    const test_str = "hello world"      => is that feature-scope or test code?
    run_test(test_str) ==> (expected value)

There's an obvious way to fix this, which is to include a new keyword to indicate a feature-scope variable. "var" ought to do it.

Let's use the word

    local

as in

    local folder = "/Users/..."

That makes sense.

----

todonow:

- separate sourcemap from source
- think about tests and test code
- return Error(x) instead of None
- decide how to bubble those up from various.

-----------------------------------

ok, can't quite believe it but a sneaky all-nighter session has given us a brand new parser.
this is super powerful and expressive, and can pretty much parse anything I feel like throwing at it, PROPERLY.

There's still a bunch of work to do:

    - error messages when things don't parse
    - source-maps for proper (iLine, iChar) reporting
    - extract code => sourcemap as before, just need to finish
    
I've also made the decision to standardise on the named-result form, i.e.

    on (r: number) = add(a: number, b: number) {
        r = a + b;
    }

This will be translateed by fnf.py into 

    add(r: number, a: number, b: number) : number {
        r = a + b;
        return r;
    }

We can extend this to multiple parameters but this is pretty good for now.


_____________________________________________________
completely restarted again; because regular expressions aren't the way to parse multiple languages.
instead, have written a sort of gonzo grammar specification.
new style of coding involving copious tests everywhere, and it seems to work.
organisation is "small to large", small first. If a calls b, b is before a.
This actually is easier to figure out than the other way round.
doing pretty well. Also this is turning into a decent rule parser.

Todo tomorrow:

finish parsing of "= defaultVal" for variables; implement "toEnd"
we need the block-finder to deal with quotes, escaped characters and quotes, etc.
so variable =defaultVal should read forward until top-level "," or ";" or "\n"

and then we need some automated way of parsing deeper down, i.e. 
variables within function params
variables within struct body
(var/struct/func) within features.

    class Typescript(Language):
        feature = ["
            'feature'", 
            "name : word", 
            "optional 'extends' parent : word", 
            "indent",
            "components : list(component)"
            "undent"
        ]

        component = [
            "(variable or struct or function)"
        ]

        variable = [
            "optional modifier : 'const' or 'var'",
            "name : word",
            "optional ':' type : word"
        ]

Even more dastardly, could you build rules just by calling functions?

    class Typescript(Language):
        def __init__(self):
        
        def feature(self):
            return sequence(
                literal("feature"),
                word("name"),
                optional([literal(":"), word("type")]),
                indent(list(this.component))
            )

        def component(self):
            return anyof(this.function, this.struct, this.variable)

        def function(self):
            return sequence([
                set("modifier", enum(["on", "after", "before"]))
                set("name", word())
                set("params", bracketedList(this.variable, ","))
                set("resultType", optional(sequence([literal(":"), word()])))
                set("components", indent(list(this.component)))
            ])

        def component(self):
            return anyof([this.function, this.struct, this.variable])

        def function(self):
            return sequence(





struct = ["modifier('struct' or 'extend')", "'{' properties(list[variable]) '}'"]

function = ["modifier(..)", "name(word)", "( params[list(variable)]",  ")", 
            "optional ':' resultType(word)", 
            "{", "body(any)" "}"

And just like that we're building a full on parser eurgh
ok anyway.

"breadth-first approach" => find the top-level structures, put the second-level chunks in a queue. There's one sort "main routine" and that is "find matching close-brace".

the bit of functionality we need in the grammar language is just a rule-name.



---------------------------------------------------
alternative representation for a function:

Function => sourceBlock, and other things.
That way you don't need to keep any other data.
Just the sourceblock.
_______________________________________________
Target workflow:
- edit markdown in vscode
- auto-save, rebuild/re-run
- console lines map to line in code
- look for wysiwyg editors that are open source
- customise to add feedback in editor

that's probably the best way to do it.

ok so next target: automatically rebuild/rerun whenever code changes.
=> let's do it.

---------------------------------------------------------------------

before we head into mentalness with logs, I think we should rethink the whole idea of logs.

There are two kinds of logs! There are those that reflect or capture runtime data, and those that communicate.

    print("hello world")

is not the same as 

    console.log("hello world")

it does not make sense for us to do the hello example using console.log or log or anything resembling logging. Instead, it will output to a stream of values.

so we will do this:

    feature Hello {
        var out: string
        on hello(name: string) {
            out << `hello, ${name}!`;
        }
    }

OK, and this is lovely, because we just have to allow ourselves to leave the { open.

So this is super nice, because it gives us a sequence. And it's the syntax we need.

OK so this is the way we make this compiler modular; we go from one form to the next.

We look into this once we get code actually running and editing from typora.


----------------------------------------------------
project dojo

cleared of all gubbins, the front room is a *dojo*. You can use it for lots of activities, including physical ones. You want the space to be completely clutter free, so you can explore it using AR. Just a place to sit, and power / cabling taken care of, so you can work unencumbered.

To get to this point, we just need to clear out the right-hand-side unit. That can be done super quickly and cheaply. Then we can get going.

dojo is a private members club - members curate "sessions" here, eg.

- morning work session
- teatime discussions
- evening demos
- conversations
- parties
- gallery
- jam session
- gig

So just keep the space totally open, and provide power and data all round the edge.

the back room is a store, focused-studio-admin workspace, backstage, green room, whatever. it's where we coordinate and enable the activities taking place in the dojo.

need the first collaborator. => carolina vallejo.



------------------------------------------------------

OK we're now generating the code correctly.
The next step is to build it: -> tsconfig, etcetc, all part of the Language module.

We need to think about a deno target rather than a ts target, that was one of the points of this. Let's think about that after a bit of ... fun.

---------------------------------------

I'm wondering now if there's an even easier way to build contexts - just copy the fucking code, rather than calling into it. Just much more efficient than the alternative.

class Context_all {
    hello(...) {
        this.print(...) // @Hello
    }
    print(...) {
        console.log();  // @Hello
    }

That's an optimisation that we can do in the future. For the moment let's just get it fucking working, right?

OK so the next step is to consolidate all those blocks and output them to a single file.
__________________
ContextBuilder: 

so basically we just define functions

OKAY. So we have Feature => Functions, Struct, Vars

Next, we have to construct a Context = List of features, plus functions defined.
Given a function f defined by feature F, and an existing cx definition cf:

    cf =:
        def => F.f, error if cf exists already
        replace => F.f, error if cf doesn't exist already
        on => par(F.f, cf), error if cf doesn't exist already
        after => seq(F.f, cf), error if cf doesn't exist already
        before => seq(cf, F.f), error if cf doesn't exist already
    
and cf / F.f are just strings.

In general

    cf := ""

The only three modifiers we actually need are on/after/before.
If we could make the before/after cases symmetrical, then we could do par(a, b) and seq(a, b)

before => if we return something, then it's an early out, otherwise we continue
after  => we need the result of the previous computation as a parameter.
replace => we need to be able to call the previous cf as a function.

Thing is: instead of storing it as a function, we could just store it as blocks already,
and let the language do its thing?

Well, let's just build the first context.


    

____________________________________________________________
Thought experiment: dealing with namespaces.

Even though our code wants to just use "print(xxx)", we clearly can't operate in global symbol space because we're usually going to be sitting on top of systems that define global symbols, so stuff will clash (eg. print in the last attempt).

So there has to be some kind of namespace object. And I think that namespace object is just the "context". Think about it:

- specifies a set of features it applies to
- defines enabled/disabled for those features
- contains a specific set of data members (persistent)
- which resolves to a specific set of data structures and functions on them

So if you have something like

    feature Hello {
        const person = "world";
        on hello() { print(`hello ${person}`); }
    }

    feature Goodbye {
        after hello() { goodbye(); }
        on goodbye() { print("bye"); }
    }

Then you could say:

    context SimpleHelloWorld {
        Hello { person : "world"; }
    }

    context ComplexHelloAsnaroo {
        Hello { person : "asnaroo"; }
        Goodbye {}
    }

    SimpleHelloWorld.hello()
    >> hello world

    ComplexHelloAsnaroo.hello()
    >> hello asnaroo
    >> bye

So you can build as many contexts as you like. And of course, you want to somehow enable a "thread-local-storage" kind of "this is the context I'm using:

    select SimpleHelloWorld;
    hello();
    >> hello world

But constructing that is going to be sort of interesting.

________________________________________________________________
on why python for fnf.py:

- deno/ts are actually different targets; too hard to write code for them both
- deno isn't the only choice, and we don't want to limit fnf to it
- python is easy to code in!



__________________________________________________________________
So here we are in our weird little fnf thing.

The original approach was reasonable, but it depends on far too much type-script kung-fu. The thing that killed it was the conflict of the global function "print" with something defined in node.js.

It was, however, useful as a "taste test" of feature-modular stuff. 

So the right thing to do is to hand-code the FNF processor, and eventually reconstruct it from the patches.
__________________________________________________________

Annoyingly, I think the namespace clash thing has made the "poke-into-global function" thing untenable.
So we should actually just generate proper typescript code, rather than trying to finagle typescript to do things.
This requires a complete rethink of the structure of this code.
Let's just lean into the "multi-language" thing, and make the processor utility feature-modular.

This thing doesn't work because you can't declare "print" because it's declared in node.js,
and that's a general issue with poking global function names. 

The only way to get around this is to move things to a namespace, which in turn means we need to just generate code.
So the way forward is this:

START A NEW PROJECT.

-------------------------------------------------------
"layers" idea.

There's "fm.ts" which  does the basic feature-modular typescript in typescript.
There's "fnf.ts" which implements feature normal form. This should be written in fm.ts
=> move it to fm.ts

But there's also this notion of "multi-point programming" enabled by "rpc" which itself is feature-modular.
There's this idea of "tasks" and the notion of "first-param-is-result" with logging, and so on.
There's the idea that logging and feature management should themselves be amenable to extension using features.
There's also the realisation that in fact namespaces might be necessary at some point.
And we may then want to do more stuff in the future.
So we need to somehow specify "this code needs these features".

Let's just keep this notion in mind as we go forward.

What's the next functionality we want? -> it's the hello world example.

hello world: print "hello world!"


-------------------------------------------------------

Idea: build "privacy" into the language somehow.
Specify that data property X is only accessible by certain features.
In other words, people can't write malicious code to access data X, only you can.
Something to think about for the pron application.

-------------------------------------------------------

Sort of feels weird to be adding this functionality in a non-feature-modular way.
I feel like we should be programming this all in fnf.ts => but we will have to rewrite it all once we're done.
Once we have the basic thing working, we can write the next version using it.

This is the way.
___________________________________________________

`fnf` is the key idea here. We should be able to take an fnf document and use it to generate code in any language, or in any combination of languages, using LLMs as the translation engines.

So actually this project should just be called fnf, and it should translate fnf.md files.

Multi-point is just the "icing on the cake".
So the idea is: we get this (microserver.fm) code working, and then we rewrite fnf from scratch, *in fnf*.


___________________________________________________


This talk: super important for noobchen.

https://cacm.acm.org/research/a-new-golden-age-for-computer-architecture/#:~:text=Innovations%20like%20domain%2Dspecific%20hardware,development%20will%20lead%20the%20way.

=> heterogenous targets, domain-specific languages, security
=> drives us towards RISC-V because of the advantage of openness in the long term

so we should be targeting FPGA, GPU, TPU, CPU because machine must contain all the above.

Which means architecture definition is actually the most important thing: make custom silicon for hardware operations. I.e. zero has to also do verilog ??

___________________________________________________
Notes on the multi-point style experiment for login:

1- "shared VARNAME" means "varname lives on server"

=> any code that manipulates or contains the shared var has to run across client/server.

So the generated rpc code we have now should be something this:

    @feature class _Login extends _Feature {
        @client @before async run() : Promise<void|undefined> {
            if (!await login_page()) return;
        }
        @client @def login_page() : Promise<boolean> {
            const entered_email = await get_input_string("please...");
            return remote(server, try_login)(entered_email);
        }
        @server s_allowed_emails : string[] = [];
        @server @def async try_login(email: string) : Promise<boolean> {
            const pin = random_pin();
            if (s_allowed_emails.indexOf(email) >= 0) {
                await send_pin_to_email(pin, email);
            }
            const entered_pin = await remote(_client(), get_pin_from_user)();
            return (pin == entered_pin);
        }
        @server @def async send_pin_to_email(...) { ... }

If a function refers to a shared variable, it's tagged as "must run on server".
If a function calls anything to do with the dom/browser, then it's tagged as "must run on client".
Otherwise, it's "uncommitted" => can run on either.

If we're running the code on the client, and we call a server-tagged function, we generate a remote(server, fn)() call and wait for the result.
Conversely, if we're running the code on the server, and we call a client-tagged function, we generate a remote(client, fn)() call and wait for the result.
So execution can ping back and forth between the two.
We can actually implement this using fetch, no websockets required. Which might be sensible really.

This is a super nice abstraction because it makes it really clear what the interaction is.

    feature MyFeature {
    client:
        ui: UserInterface = new UserInterface();
        def login_page() : boolean {
            const email = input(ui, "enter email address");
            const pin = try_login(email);
            if (pin == "") return false;
            const entered_pin = input(ui, "enter pin");
            return (pin == entered_pin);
        }
        def get_pin_from_user() {
            return input(ui, "enter pin");
        }
    server:
        users: string[] = [];
        def try_login(email: string) : string {
            if (s_users.indexOf(email) >= 0) {
                const pin = random_pin();
                send_email_to_pin(pin, email);
                return pin;
            }
            return "";
        }
        def send_email_to_pin(...)
    anywhere:
        random_pin() {... }
    }



    






__________________________________________________

Today: 
- got hand-coded imports working. tomorrow: automated.
- target for monday: ready to write the first actual server feature

Ideas for features:

actually structure by functionality, across client/server boundaries.
so don't reify server/client status, as the first set of things did.
more like:

- "to serve a file, we need this on the server"
- "to do rpc, we need this on the client and this on the server"

This is why I think "roles" need to become first-class citizens of the language.

    client: blahblah
    server: blahblahblah

We want to see the code for the two locations in the same place, collected by functionality. Otherwise it makes no sense; you're only showing one side of the interaction.

Mucking about with expressing login/authentication logic:

    feature Login extends Feature {
    client: 
        before run() {
            if (!login_page()) return;
        }
        def login_page() : boolean {
            const entered_email = get_input_string("please enter your email address");
            return try_login(entered_email);
        }

    server:
        s_allowed_emails : string[] = [];
        def try_login(email: string) : boolean {
            const pin = random_pin();           // 4-digit random pin
            if (s_allowed_emails.indexOf(email) >= 0) {
                send_pin_to_email(pin, email);
            }
            const entered_pin = get_pin_from_user();
            return (pin == entered_pin);
        }

        def send_pin_to_email(pin: string, email: string) { ... }
    
    client:
        def get_pin_from_user(): string {
            const pin: string = get_input_digits("please enter the 4-digit code we emailed to you", 4);
            return pin;
        }
        def get_input_digits(...) { ... }
        get get_input_string(...) { ... }
    }

See: now remote execution goes "downwards" into the language as well. But then again that's always what we wanted. The pattern's interesting though isn't it - we think we can implement it using fm, but it turns out we kind of ... can't.

the fm implementation *itself* wants to be feature modular, as do the tools. It's frustrating that they're not. But non-fm ts is the language we're bootstrapping.


--------------------------------------------------------------

Summary of today's work:

- source map as a map rather than in the code
- generate import_FeatureName.ts files that import everything in the right order
- generate import/all.js 


-------------------------------------------------------------

Summary of yesterday's work:
- fnf now generates correct declarations
- new concept for hello-world demo
- idea of str<T> capturing sequential and parallel values
- idea of making log into out$
- editor format for features 

--------------------------------------------------------------

another blinding flash of light: 
everything becomes simpler if we think of everything as a function returning a stream.

so for instance, the demo is just something that outputs a stream of strings : the console.

so instead of 

    def demo() { out$ << "hello world"; }

you would do

    def demo(out$ : str<string>) { out$.push("hello world"); }

OK, this is a little groinky, I'd rather do "<<" - but in fact it might be that we can solve this quite easily with a bit of regexps upfront:

    on out$ : string << demo() {
        out$ << "hello world";
    }

I can just compile that to typescript:

    demo(out$ : str<stream>) { out$.push("hello world"); }

AH, we have to write this shit in fm.ts, otherwise chaos. But let's get it building first, then we/someone can use it to write v2.

The thing that I think might be interesting about `str` is if it wasn't just "here is a sequence of T": what if it could also represent parallel invocation.

So no matter how things work out, we can see exactly what happens to the sequence we're creating.

So like you could click on "out$" somewhere and see this:

    10 9 8 7 6 5 4 2 1      < Countdown.countdown()
    hello world!            < Hello.hello()
    kthxbye.                < Goodbye.goodbye()

So maybe `str<stream>` is kind of like the really complicated logging stuff - there's actually something super interesting there. That's the core data structure: the stream.

    - captures time sequence
    - captures parallel invocation of stuff
    
I like this idea, I like this idea. How about: if we don't get input for X seconds, kthxbye. => and logout or whatever.

So the stages are:

    1- hello world
    2- hello you (input name)
    3- goodbye + reset
    4- countdown alongside

Yeah there's something here.

Demo: here's the basic thing
Hello: just say hello world
 +- Greet: get the name first
    +- Goodbye: if we don't type fast enough
Drumroll: drumroll before.

This is super cool, let's try this, because it has concurrency, but is simple.

------------------------------------------------

zerp formatting idea: 

instead of trying to draw a "tree", which is complex and doesn't feel quite right yet, do this: 

Show the current feature doc; then below it, oldest first, the child features: but just a name and a one-line description per feature. Clicking on those expands them in-place, in the same editor.

Super simple, no jumping around, easy to zoom in and out. Works on mobile just as well. 


-----------------------------------------------------------------

Another thought about R&D strategy:

Backend track:

Develop an intermediate bytecode form similar to SPIR-V (look at their design for inspiration); similar enough that we can translate to and from SPIR-V. This bytecode should, however, have array and stream stuff in it.

We should then be able to compile this bytecode to WebASM, WebGPU, ARM, SPIR-V, whatever, and so on, with minimal fuss. 

Backend track is parallel to the core track.

-----------------------------------------------------------------

okay so we figured out how to do symbol imports (thanks you-know-who)
so now we have to maintain a global table.

which brings us bang smack into ... namespaces.
For the moment I'm going to just make one global namespace, but it's something we have to address properly in due course.

Right now, I'm going to create a single "all.d.ts" file, which everyone will import, job done.

------------------------------------------------------------
Achieved: 
- tree of .md features in folders
- renames features to _features, writes boilerplate
- automatically does import, declares
- move to feature X extends Y; syntax, so no trailing `}`
- move test to method of feature

Tomorrow:
- move declares to .d.ts files
- compile tree using tsc / tsconfig

------------------------------------------------------------

Achieved: processes .fnf.md and outputs .fm.ts;
runs tsc and processes console log to output .md filename/line numbers.
Not working yet: 
- run the actual tests
- auto-run whenever .fnf.md files change
- import from fm.ts (think it's not using the right config).
- run on full folder
- declarations into .d.ts somehow

---------------------------------------------------------
Tomorrow: compile the tree you produce, then run the tests, issue report.
Then do a tree of features.
Then move the client, server and shared code across to it. 
Get on with it.

--------------------------------------------------------
Brief aside to record a new-ish intuition about streams.

A stream is a time-series, right? It's a list of pairs: (time, value)*i*.

An array is a special case of a stream where t*i* = *i*, where *i* starts at 0.

An array slice is a case where *i* starts at something other than 0.

A sparse array can be made by concatenating two arrays with non-intersecting ranges, so the first range is i E ( a .. b ) and the second is i E (c .. d) where c > b+1.

If we constrain t*i* to be any integer (let's say 64 bits for argument's sake), and tie the stream to time by setting a "time step" to be a rational number of seconds, n/d. So we can go from *i* to *t* (actual time) using t = i * n/d, and of course from t to i using i = t * d/n.

If we set up d/n so that all elements of the array map to the range t E (0..1), then we have a texture sampler. 

What this means is that streams, sparse arrays, plain old arrays and texture samplers can all be represented by a single data structure.

That structure looks something like this:

    slice = (num, den, iStart, nElements, data)
    stream = list of slices

So for instance, if we have an audio stream playing at a fixed speed of 44.1KHz, then there's just one slice:

    (1, 44100, 0, nSamples)

On the other hand, if we play n0 samples at 44.1 Khz and then n1 samples at 48Khz, the output will look something like this:

    (1, 44100, 0, n0) • (1, 48000, n0, n1)

Where `•` is the concatenation operator (and should be allowed as it's a character).

So there's an abstract object called a stream which is the list of these slices; and we can operate on these objects using a range of different operations; but fundamentally, that's what we're doing when we specify time-domain behaviour.

In the actual system, a task holds a rolling "window" onto the abstract stream, throwing away stuff it no longer needs. It can hold some data stretching back into the past, and for input devices (such as audio incoming) it by definition doesn't have anything going into the future, but for algorithmically generated streams it can evalute at any time in the future.

-----
short tangent into latency, seeing as we're here:

we can represent the speed of a computation using a rational time duration num/den.



----------------------------------------------------------------
What we're actually doing now: `fnf.ts`.

fnf.ts reads blah.fnf.md files and outputs blah.fm.ts files.

----------------------------------------------------------------
Most efficient route forward:

1- fm.ts to get zerp working; literate fm.ts with LLM translation.
2- use zerp to write zinc in fm.ts (zero to arm multicore).
3- buy a 192-core server and write a hypervisor
4- add some GPUs and get the GPU stuff working

So fm.ts should be literate from the ground up. That's just the obvious thing, there's really no big deal to it. But everything should be literate, even the fm.ts processor.

So the *core* of the system is the .md pipeline.

----------------------------------------------------------------
Woke up this morning definitely feeling like I want to write the .md pipeline,
convert "fm.ts" to straight .ts, and feed back errors using a zerp-like workflow.
Of course, until the web editor is working, the workflow is awful.
So it's a chicken-and-egg type issue. Maybe therefore it's better to plough forward
with this workflow until zerp is working, and then use LLMs to transform the code somehow?

I mean that's the obvious thing.

Also however I'm not sure that deno's the totally right choice for this.
But let's plough on, right? The next thing is testing.

testing is not going to be a normal thing; it's meta, for sure.
as is logging. I think we just note down that "testing, logging and other meta-features live in their own space".

So should we just do fm.log(...)? I think that's sensible.

Same with testing: we should just do fm.test

These are not client code, these are workflow things, so let's put them in fm.ts.
That makes the most sense.

----------------------------------------------------------------
magpie stuff: 
beat detection: https://github.com/dodiku/AudioOwl

interface is: drop new track in, find beat, first-beat
real simple hummingbird sequencer: number key plus up/down arrow, enter to go to it
space to switch between loop/forward

stem-separation extracts the data just for the current loop, then continues in background.
so you get the stems for your current loop pretty much immediately.
and then it's basically just hummingbird mixing, but with the stems you choose.

something like this anyway.

----------------------------------------------------------------
fm.any

concept: write literate feature-modular code in .md files;
generate output code in any language (including for polyglot projects)

Input:

    feature XYZ extends ABC
        on blah
            blahblah
        after blah
            blahblah

Output:

    standard typescript/python/cpp/whatever.

I mean, this would be crazy cool, would it not? No reliance on decorators, just write code, voila.
Logging everything working properly, I like the sound of that, and it's just typescript code running in deno.

Maybe that would be cool to do. Just write fm.md, you get typescript

```ts
feature MyFeature extends AnotherFeature {
    def myFunction() {}
    replace myFunction() {}
    on myFunction() {}
    after myFunction() {}
    before myFunction() {}
}
```

----------------------------------------------------------------------

idea: home systems as a good market:
- clearly something needed here
- what's the ultimate home lighting control system? 
    => tap on a zone, ask for the lighting to change
    => eg. point to the coffee table or the sink, say "lights up here"
- requires "omniscient AI camera watching everything you do without wearable camera"
- not creepy at all honest: all controlled by your own code innit
- no headset required: just all-seeing home alexa now with sam altman / us built in

=> make this trustable and verifiable using the three principles: loyalty, discretion, transparency

oh btw zero / zfg / do the math

----------------------------------------------------------------------

test: clients should run "shared" tests, but servers should only run things they can run when solo.

    @test test_name() {
    }

Now that's fine, we can create lots of different tests.
Most of the time, a test will be a "replay" of a failed run, which we then fix.
start at state0, sequence of operations, end up at stateN, check condition => pass/fail.

    @fixme failing_test() {
    }

I think any thoughts about whether stuff should be in fm.ts or outside fm.ts should default to "inside".
fm.ts is the engine. We can always look into extendability later.



--------------------------------------------------------------------------------

ok then testing. HOWTO.

Can't use a virtual _test() method; because if you don't define it, it calls the parent.
So we need a decorator to mark any method as a test.
Which in turn means that we can support multiple named tests.

    @test async _test() : Promise<boolean> {
    }

    @test _test() : boolean {
    }

Both are totally fine. Let's do that.

OK: so test decorator. But only one per feature to start with.
Done. The next thing is, though, where and when do we run the tests?

The point of a test is that it runs "before" the main application.
But what if the test is actually testing some kind of interactive / real time / multi-machine thing?
We want to do "full integrated" tests, right? 
So this is a moving feast.

Anyway, let's just fill in the tests for each feature.
The interesting thing is: when you write a test for the top-level feature, there are no lower-level tests.
As you add behaviour, you're adding new tests, and potentially breaking higher-level ones.
So you're saying stuff like: "this new feature breaks tests in the parent, but that's fine because XYZ"
which means that you actually have to be able to point to individual tests, which means ... I don't know.

Two tenets:

"a test is written at the time of the creation of the feature, but must continue to pass when the feature is extended"

"if a new feature causes an existing feature to fail its tests, then we create an *adapter* to help the test to pass"

What is this mysterious adapter? Simply, it's whatever features you need to fix the problem.

Often, you'll find that you'll need to modify the original test to make it pass when the feature is upgraded.
This (obviously) extends to the documentation as well; so you now you can say,

"the old behaviour of the system was (X); now, with a slightly different invocation, it's ..."

We could therefore be devilish and use @replace / @after / @before / @on.
What's the worst that could happen? Just extend the test to do whatever.
In parallel? why? Let's make that all work properly, I mean what's the worst that could happen?

We want to call something and see a full readout (graphically helloooo) in the browser.
So let's make that an absolutely beautiful experience: webIDE ahoy.

pulse.
great name.
also:

*magpie* for the sample chucker-together hahaha

I think that's the thing you do: decorate the first thing "test", and test() will just run itself, as it ought to.
Fucking brilliant; just do it that way.

So we don't need a particularly savage test harness, we kind of have it already.
test() just gets made more sophisticated through normal extension.
FINE FINE FINE.
And it either throws, returns false, or returns true, plus a console as well obviously.

So we don't need anything, just test() as per fucking normal.

Let's try it.



---------------------------------------------------------------------------
next steps:

1- get testing framework running
2- test logging across multiple machines, async, the works
3- literate programming: md=>ts
4- vault function
5- interactive editor (zerp)



------------------------------------------------------------------------

returning to work:

- fm.ts is the right path forward. 
- end goal is machine translation to zero.
- initially, login (vault) and then IDE
- IDE is just zerp + feature explorer

where we are:

- logging is working in RPC. bit more work to test mt then done
- testing framework is important; not serious unless we have that

so I think next is testing. cool!

strategic:

- hire dominic to help write the compiler; +1 junior (he finds/manages)


-------------------------------------------------------------------------
What you want is:
I'm calling A and B in parallel, I want some kind of indication of that in the log tree. 

Log = (Log|Line)[];

If you really want this to work, you have to be absolutely ruthless about tracking concurrency.

so if I have async functions A and B, and I call them in parallel like this:

    await Promise.all(a(), b())

Then really I need to wrap the a() and b() functions with a call to async_log.

But if I'm doing this:

    await a();
    await b();

Ideally, I just pass the log property in as a "silent parameter".

I'm definitely overthinking this shit. But never mind, let's overthink it, and get something amazing.

----------------------------------------------------------------------------

The logging thing works like this:

1. There are two basic "modes" of modifying a program:
    - "additive" : we're making something "new"
    - "restorative" : we're fixing something that's broken

These two cases are subtly different, even though they both involve the same steps:
in the first case, the program is already doing what it says on the tin; we're adding to its mission.
In the second case, the program isn't doing what it should be.

"what it should be" is the whole test/spec/doc thing we invented in zerp.
So really, we shouldn't spend too much time agonising about the right console workflow here,
because in fact it depends on the zerp workflow, which is different to the normal one.

So the right thing to do for now is to be able to turn on/off logging on feature-by-feature basis.

feature-granular logging. I'm working on a new feature F, so I want to see its logs;
so everything it calls, I want to know about.

every log statement should output in such a way that the log line comes through, so we can feed it back.
Thing is: do we really want to know what's going on in every function?

When we look at the console log in the browser, we want to see:
- output from the function(s) we're writing : i.e. the new feature
- output from any failures that happened, with their location.

So let's just issue warnings and errors, not status log messages unless absolutely necessary.
My feeling is: just keep it feature granular, we don't need to know about other stuff.
We want to know how the feature behaves, and all of that information is contained in its code.

OK: that makes it fairly simple, right? this.log()  => does the same thing, but only if the feature's debug switch is enabled.



-----------------------------------------------------------------------------------
dawning realisations about async/parallel programming:

if you do await X, you're actually saying "please execute this synchronously"
if you *don't* await X, you're saying, actually, fork execution here.

The zero model, saying:

- everything synchronous by default
- map / reduce / filter work in parallel
- on extends behaviour in parallel (add 'combine' operation for non-void-returning tasks)

works super nicely to specify behaviour.

logging is an interesting thing. There's actually two cases here:

1- where you're developing some new code, and you instrument it heavily. once you're done, you distill a test.
2- something goes wrong with "old" code, so you re-instrument it, and voila.

You kind of want to be able to turn logging on or off on a feature-by-feature basis.
I think that's a super interesting approach.
You could use "this.log" which redirects the best function, or nothing.

I kind of actually really dig this approach, because this.log can hide all kinds of shite.
So when you're developing a new feature, you turn logging on for that feature, and you get everything for "free".
When you finish, you turn logging off, and all the logging statements stay there, but just compile to nothing.

________________________________________________________________________________
moving closer to logging nirvana.
we've now managed to get it so log messages on the server can be read on the client
we have an expandable console.
next steps are:

1- implement log using FM, so we can just use 'log' on both server and client
2- wrap the async console caller around the earliest part of the serve chain
3- be able to turn logging on or off per feature
4- get suffixes working again, via the async stuff

Then local storage. fm is actually good for a bunch of stuff. I like it a lot.
I'm starting to get the hang of fm, which feels good.

________________________________________________________________________________
Productive day:
semantic change:  def, replace, parallel-on. works!
tree-logging: doesn't do threads yet, but that's next.
want to attach the log to the request:

    log(request, msg);

and then we can send back that stuff to the client, which would be huge.
We're actually not interested in the details around it, as much as we are what's inside the function.
That function doesn't know anything about the calling context, so it's harder.
you just need to pass the log into the function somehow.
but then that has to pass that one further down, and so on.
So I do need some kind of per-thread object.

________________________________________________________________________________
semantic change:

    @def : define function for first time (error if already defined)
    @replace : replace existing definition (error if not already defined)
    @on : if void-returning, run new function alongside old one, finish when they both finish
    @before : sequential before, with drop-through
    @after : sequential after, with access to result

we could do

    @on : define if not already defined, replace if non-void-returning, parallel-aug if void-returning async.

we have the mechanism to do def/replace/on properly.
and it's early enough to make that change, so let's do that.

OK let's think about this multi-module dependency issue.
client extends shared, but not vice versa.

that's the deal. so there's "shared-run" which is not the same as client-run.

There's a weird issue of logic here, because the idea of a shared run is suspect.
right now all code is client-viewpoint-first, so there's no real "shared" / "client".
Just client stuff = stuff that only runs on client.
so client extends shared, not the other way around.

---------------------

Actually I think testing is the next "most important thing".
Particularly, the connection of testing to features.
Testing and logging are intimately connected. We need a proper next-gen solution.

Idea of "concertina-log": when you're developing something new, you add "log" statements.
These output to a line buffer, and print to console.log.
When we're happy with things, we save the buffer as "reference;
and then change all log(x) to silent_log(x).

silent_log generates the console line, and checks it against the current line index
(which monotonically increases). If we find it at >= that index, we "succeed" and continue;
otherwise, we have an error, and we stop and issue a "test failed" error.

I think we definitely also need to look at a "shared" logging system that does two things:
1- allows recursion / detail hiding
2- puts all interacting logs into the same (spreadsheet?) structure
3- establishes a common ordering / clock system.

Again, using feature-modular logging rather than console.log seems to be the right approach?

    log(x);
    log_silent(x);

So we have two buffers:
    the check-log (never changes; silent_log checks against)
    the new-log (output from "log")

Let's do it! Via fm, in shared.

------------------------------------------------------------------------------
Dig this bit of gpt output: how to establish a WebRTC connection

Example Scenario:

    Peer A and Peer B connect to the signaling server:

    They use WebSockets to exchange signaling data.

    Peer A creates an offer and sends it to Peer B via the signaling server.

    Peer B receives the offer, creates an answer, and sends it back to Peer A.

    Peers A and B exchange ICE candidates via the signaling server.

    After the connection is established, the signaling server is no longer needed:

    Peers communicate directly using the WebRTC data channel.

How would this look in code?

    on webrtc_connect(a: Device, b: Device, server: Device) {
        connect([a, b], server);
        create_offer(a, b, server);
        receive_offer(a, b, server);
        exchange_candidates(a, b, server);
        webrtc_connected(a, b);
    }

    a.doSomething(...);
    b.doSomething(...);

=> that would be interesting, would it not... have to create that somehow.
=> highly convenient notation, if each device is just an object with that interface.
server.doSomething()    => is the same as. So yeah that would be super fucking cool.

Right now the syntax is

    remote(server, fn)(params)

    on(server, fn)(params);



------------------------------------------------------

Monday: a good idea would be to look at storage.

Let's build a vault with the following characteristics:

- login using email, 4-digit-pin
- load(file), save(file, data)
- local cached version is used if it exists, otherwise reload
- server updates us with new files via websocket

We could do a bunch of things. We could look at user interaction...
We could look at authentication and file serving.
We could make offline mode work seamlessly with all of this.
The lower down offline mode is built, the better it's going to work.

Of all the lovely things we could build, what's the most exciting?
not the vault, though that's exciting.
it's the multi-point thing. Clearly, right?

Simple demo: tap either the laptop or the phone screen to switch from blue to orange.
Both laptop and phone switch to the same colour. I like this demo.

Also, we draw the logo at the center of the screen. Come, let's do it.

Some system of design that allows mobile and laptop to both work with the same codebase.
I don't know, man, it's hard. But again, maybe it's super easy, because of features.



So really, it's the `@shared` decorator. Loving it.
And for that to work, we need websockets between things, and rpc via websocket.

    remote(machine, func)(params)       -> not fucking bad.

And we can use this pattern again, eg.

    all(func)(params)                   -> run on everything

    best(func)(params)                  -> run on best available

Now see that's interesting: in actual fact, the `best` algorithm should be able to read the parameters of the function to decide where to run.

    x = myFunc(y, z);                   -> x, y, z are shared vars

We should go:

    - which machines are x, y and z live on / available on
    - if machines exist with all, rank by closest / fastest connection to


OK: So that's the demo tomorrow:

    - switch laptop and phone between blue / orange when you tap either screen

Debug this system as a singular unit. That's the way: go immediately to difficult test case.

"this happened" - drop the event into the pond.

    user pressed button => flip colour
    colour changed => redraw background

    flip_background() => run on everything, everyone gets shared object.
    we call deterministic functions on everything simultaneously.

    so there's this shared property called "colour"
    clients read it to change their background
    and call flip when they click on their screen.

    let's make that work tomorrow.





___________________


Some sort of brooding/looming insight into the nature of logging / testing newniceness.

When you get to a happy place, you sort of want to pause and reflect.
So it's just like: log stuff, keep a snapshot of the code and the log.
And then make it disappear. In other words, all the console.log() calls up to now should disappear. All we should have back is the "running" thing.

Under the hood, it's still logging, but it's logging to a silent "background" log.
We compare this log to a snapshot of the log saved at the last happy place.
Basically, we should find every line of this log in the snapshot, increasing monotonically.
i.e. every line i should map to j in the source, where j increases.

    console.log(blahblah);

What if instead we have

    log(blahblah) { console.log(blahblah); silent_log(blahblah); }

    silent_log(blahblah) { add to lines; }

each run: store a snapshot.




___________________
Good progress today:

1- managed to get remote function calls working! I can define a function and call it on any Device (which is what I called a Server). This seems like a good first step. Currently only via fetch, but next step I guess would be websockets.

What's nice is the discipline of building things by adding new features. Slowly starting to get the hang of it.

Thoughts:

- "on" semantics. Idea of "def" and "on" where "def" defines and "on" extends.
- "replace" to override completely

For void-returning functions, on x y should just run y in parallel with x;
and we should return a promise that waits for both x and y.

For T-returning functions, on x => R { ... } should run the new function, get the new result, and combine them in some way. So it should be:

    @feature f1 
        @on run() : number { return 1; }

    @on feature f2
        @on run() : number { max(newFn(), this.existing.run()); }
        @on newFn() : number { return 2; }
    }

We just need the right notation.

    @on fn() : number {
        
    }



----------------------------------------------------------------------------------------

OK. We're going to do the vault, but our order of development is:

1- be able to start the website even if the server is down (solo mode)
2- cache files in a local db, so can access when the server is down

----------------------------------------------------------------------------------------


Let's call this concept a "Vault".

A Vault is a single executable file containing encrypted data. To access the data, you run the executable, then log into it via HTTP on localhost:whatever (give it your email, it sends you a code, you give it the code, you're in). Once you're in, you can "see" the files it contains, and access them using a simple websocket based API (ls, cd, read, write).

This is a super secure way of storing information, because there's no "key" or "password". Whoever holds the file, they can't access the data without also controlling your email address. We can make the login process arbitrarily complex.

So the API is something like:

    login(email);       // send one-time-pin to (email)
    code(code);         // 4-letter one-time-pin
    logout();           // log out on this machine
    files();            // get a dictionary filename => type
    read(path);         // just read the data
    monitor(path);      // call-back when it changes
    lock(path);         // lock for writing (steals lock)
    write(path, obj);   // write to file (fails if someone else has lock)





----------------------------------------------------------------------------------------


Thought experiment: scaling from one machine.

I have a "locker" which belongs to me, which contains a bunch of code and data.
It's private to me and me alone; if I run the locker, and log into it, I can view the files and run the code.
I can sell access to it (a paid login), and people can access the files in the locker.

So this is the first concept: a safe data store.

----------------------------------------------------------------------------------------

Goal for next week: multi-point.

Mac mini
Ash laptop
Phone

all knitted into one application, that works whatever the connection environment.

----------------------------------------------------------------------------------------

Next step:

the simplest possible "call any function" console interface.
you type it, we run it wherever we damn well please.

use this to implement login.



----------------------------------------------------------------------------------------
Ideas to explore tomorrow:

- implications of, and limitations to, the "local-first" idea; is there a pragmatic middle way?
- "the movable feast" idea: that 'server' could move from one machine to another
    - a network that runs multiple parallel tasks, distributed across available machines
    - thus fault-tolerant; if a machine disappears, we can redistribute its workload
- idea of the "persistent process" : object-dictionary and computations, owned and accessed

OK: one of the implications of the local-first thing is that if I have my browser hitting a localhost server, all computations are actually taking place on the same machine. 

So, for instance, running an LLM. If you can see the server, you use it, if not, run it locally.
It's the same computation and the same resources, just adapting to their local performance envelope.

So there's this idea of a Context. It's ideally a single file, with all the structure hidden inside.

It contains:
1- a file system: actually just a dictionary mapping (path) to (object)
2- the code, including all features we use

To start with, the Context is just a dead file, and you're not connected to the internet, so you run it. This loads in all the active tasks and the filemap, figures out what roles there are within the context, and assigns them all to machines in the network.

So in the chat example, a context contains:

    a user authorisation list [(username, email)]
    code to allow anyone to join the context
    a set of "roles"

A "role" is something like "user_asnaroo" or "client" or "server". We want shared code to describe the interaction between those roles, regardless of where they're instantiated.

So we can create four users and a server, and run all those roles on this machine, if we want.
Super useful for testing, of course. 




--------------------------------------------------------------------------------
Today was a good day: got the first fully fm client/server pair running and talking!
There's a client.fm.ts, a server.fm.ts, and a shared.fm.ts,
It turns out that if you get things right, you can have "client+shared" or "server+shared"
and everything ends up in the same module-scope namespace, so function poking "just works".
But that's a decent milestone really.

By splitting the code into client, server, and shared, you ensure that you don't send more code
to the client than you have to, you don't run client-only code on the server, but wherever there's
interaction between them, you work "above the fray" in shared.fm.ts.

Code in shared.fm.ts is really now where the design fun lies. 

Good article on local-first (spotted randomly on twitter)
https://www.inkandswitch.com/local-first/

Lots of things are quite sensible here. This is a fun space to experiment in, so let's.

--------------------------------------------------------------------------------
Thoughts on the "shared" programming model.

The key idea of shared-mode programming is that our scope is "above the fray". 
Our physical cluster consists of multiple available resources, both data and processor, 
and we wish to distribute a "virtual cluster" of 'tasks' (streams / live variables / shared-vars) across those resources.

The key observation is that we should be able to dynamically re-distribute those tasks when the cluster changes, either by adding or removing a machine.

Rather than try to be completely peer-to-peer, we'll work pragmatically in a local-first way, but with the server helping out as much as seems sensible.

We want to enable the good stuff, like:

    - works even when we're offline
    - super-fast response (work on local copy with eventual dispersal)
    - simple programming model
    - distributes well across machines

So this "machine" idea we'll actually call a "role". It's kind of like a ... "virtual server"?
I don't know what to call it. But we can move it from one machine to another.

So for example, I could "simulate" a chat with 2 users by spinning up 2 "nodes" running on my local machine. No worries. OK, so I totally dig this approach. It means that actually your local file environment is super important, you have your own stuff running on your machine talking to your local browser through localhost, and that is a normal and acceptable way of doing things. The server might go away and come back, but that's fine.

So when we set you up, we set you up with a server that runs on your own machine, and you talk to it via your browswer pointing at localhost, and *it* talks to the remote server at microclub or wherever. So you're never going to an external URL, only a local one.

The server is there as a machine that is "perennial" - it can always be relied on to be working and have the latest agreed wisdom, if you can get to it. When you can connect, you add your "trace" to the pool, and read back what relevant changes there have been. Both sides need to then resolve conflict somehow (I don't know, maybe... use AI to do it?) through a massive hand wave.

So the architecture is:

- maintain connection to server; note when it goes up and dowon
- join a cluster, establish websockets via server

I also quite like the idea that there's just a sort of "HTML stream" for the UI of each running "thingy". HMMMM so you can turn any object into html, and zap that html over to a browser which just displays it somehow in some framework UI. 

--
challenges are:
1- user authentication. that's next.
2- find clusters
3- join cluster
4- run stuff

So first thing should be:

1- converting an object to html, and having the html modify the object
    1a - to "toHTML" function that we can keep overriding and adding to...
    1b - a "fronHTML" pipeline (via listen etc) that calls functions

Fundamentally, the UI is going to call functions, and it's going to call them through this great proxying system that lets us surround every damn function call with a bunch of stuff, turn-on-and-offably, with small-grained control. Like, turn off logging, graphing, everything, just run clean, or turn on just graphing, for groups of functions, or features, or whatever.

It's just potentially SO COOL.

Let's think about "pots" - it's a folder that a group of people shares.
You can gain access to that folder; once you have access, you have a local copy of whatever you're interested in (subscribed to).

Access control of a "zone" or "box" rests with the owners. It's like a whatsapp group with a bunch of files. It's out there somewhere (on a server maybe) but encypted so only the owners can access it. Once we access it, we get local copies of everything, and ensure that we can keep working even if the server disappears.

here's an empty room "room1" owned by asnaroo

It's a persistent computation that's carrying on, its state evolving, every time it runs. It's effectively an autonomous process. It can shut down for a long time, but then when someone runs it and joins it, they get allowed access, and thenceforth they can subscribe to any file, and edit it any way they want. It's AMAZING.

This concept of a shared object-state-set (name => object) OMG that's all it is. 

    object["path"] => just gives you the object.

    listen_object([object["path"], uiState], () => { display(object["path"], uiState); }

There's a UI on your local machine that talks to your local object, and you get mod
requests from other machines (via the server).

--------------------------------------------------------------------------------

Okey. Now for multi-point programming.

The obvious and most fun thing to do is to look at the hello name example.
What should the code look like?

    @feature class _HelloClient {
        @server @private @persistent("users.json") static users: any;

        @on client_main() {
            let name = input("name");
            let message = greeting(name);
            print(message);
        }

        @on greeting(name) { 
            if (recognised(name)) { return "hello, " + name + "!"; }
            else { return "fuck off"; }
        }

        @server @on recognised(name) : boolean { 
            return _HelloClient.users[name] != undefined;
        }

        @on input(..) { some html stuff }
        @on print(..) { some html stuff }
    }

`@server` : the property or function lives on the server
`@private` : the property cannot be sent to any other machine
`@persistent` : the property gets loaded from the file at startup, and autosaved when it changes.

So let's see how a chat program would work:

    @struct class Message { 
        user: string;
        text: string;
    }

    @struct class Chat {
        title: string;
        messages: Message[];
    }

    @feature class _Chat {
        @server @persistent("chat.json") static s_chat : Chat;
        @server @on post(msg: Message) {
            chat.messages.push(msg);
        }
        @on client_main() {
            display(s_chat);
        }
        @on display(chat: Chat) {
            ... generate html ...
        }
    }

`on_changed` subscribes the client to a specific variable; on the client.
I kind of think we should do subscriptions based on paths.

I think we should use websockets for everything.
Also, under the hood. What's the correct abstraction?

    monitor(path, (obj) => fn(obj);)

    monitor("chat.json", (chat) => display(chat);)
    







-------------------------------------------------------------------------------
Some daylight falling on poke-able constructors. Found a method that works.
This week goals:

1- now that we have a pathway to auto-construct, finalise Colour example.
2- get the simplest, most natural form of "multi-node" programming working.
  (which in this case would be client/server)

stretch goal
3- demonstrate a basic chat program running in this environment




TEMP:
//-----------------------------------------------------------------------------
/*
    feature RGBColour {
        struct Colour { r: number=0; g: number=0; b: number=0; }
        on add(c1: Colour, c2: Colour): Colour {
            return Colour(c1.r + c2.r, c1.g + c2.g, c1.b + c2.b);
        }
    }
*/

class Colour { r: number =0; g: number =0; b: number =0; }

declare const add_colours: (c1: Colour, c2: Colour) => Colour; 

@feature class _RGBColour extends _Feature {
    @on colour(r: number=0, g: number=0, b: number=0): Colour {
        return construct(Colour, {r, g, b });
    }
    @on add_colours(c1: Colour, c2: Colour): Colour {
        return colour(c1.r + c2.r, c1.g + c2.g, c1.b + c2.b);
    }
}

//-----------------------------------------------------------------------------
/*
    feature RGBAColour extends RGBColour {
        struct Colour { a: number=1; }
        on add(c1: Colour, c2: Colour): Colour {
            return { add(c1, c2) .. c1.a + c2.a);
        }
    }
*/

interface Colour { a: number; }
@extend(Colour) class Alpha { a: number = 1; }

declare const colour: (r?: number, g?: number, b?: number, a?:number) => Colour; 

@feature class _RGBAColour extends _RGBColour {
    @on colour(r: number=0, g: number=0, b: number=0, a: number=1): Colour {
        return construct(Colour, { r, g, b, a });
    }
    @on add_colours(c1: Colour, c2: Colour): Colour {
        return colour(c1.r + c2.r, c1.g + c2.g, c1.b + c2.b, c1.a + c2.a);
    }
}

function main() {
    let col = new Colour();
    console.log(col);
}

main();
_____________________________________________________________________
Thoughts on multi-point.

we have bits of state that are owned (published) by various nodes
we want to specify operations on those *bits of state*, regardless of where the state is stored, or where the operation takes place.

Yo define a "machine" using this syntax:

    node Drone
        cam: Image;                // stream of incoming images
        target: Location;          // stream of commands
    
So we can write simple, matter-of-fact stuff like

    feature DroneFollow
        on follow (drone: Node, person: Image, distance: Scalar)
            drone.cam >> image: Image
            find (person) in (image) >> region: ImageRegion
            find location of (region) relative to (drone) >> location: Location
            (location, distance) >> drone.target

enteresting, or

    feature DroneFollow
        on follow (drone: Node, person: Image, distance: Scalar)
            image: Image << drone.cam
            region: ImageRegion << find (person) in (image)
            location: Location << find gps coord of (region) relative to (drone)
            drone.approach << location, distance;

These are just streams being hooked into one another; there's no mention of where the computation takes place, *except* where we refer to a stream that's bound to a particular node (in this case, the input `drone.cam` and the output `drone.target`). And because only those variables are physically 'pinned" as it were, the others can exist anywhere.

So the decision about where each computation takes place can be based on:

    - which machines are fast enough to run the workload?
    - which machines have enough spare capacity?
    - how long does it take to get data from point A to point B?
    
So "expensive" operations such as `find (person) in (image)` can end up moving around.

In this example, imagine that we start with an inexpensive drone, that can't do much more than stream a camera feed back to base. In this case, we'd want `find person` to run on the server, and ... stream the camera feed back to it. Not especially controversial.

But, we moan, well, all that video information is a pain because it uses bandwidth, and it limits how far away we can fly, there's latency, etc etc.

No problem, we go out and buy a super drone that has a bunch of GPUs on board. Hey presto, now the whole of `follow` can run on the drone, the server just sends it `follow` commands (the code doesn't have to change; we just replace the call with a proxy).

This is, I think a super cool capability, and it's what we're building this week.
Once we have this, we're going to write proper client/server code that looks and feels sensible.

_____________________________________________________________________
There's a flavour of this where all nodes are explicitly specified.
So you have client ("nothing") and server, and any other machines eg. drone.

I don't mind this for now.

When we declare a variable "shared", we assign it to a specific node.

    So we say

    @shared(server) var xyz;

(inside the feature obviously)

    and then we can use xyz wherever we like.

Functions are "pinned" as follows:

    if it modifies (var), then it has to run on var's owner. 
        we generate a proxy on the client that forwards to the owner.
            we standardise on a websocket substrate.
    if it reads (var), then we have to subscribe to var's owner.

So we have

    class Chat {
        users: User[] = [];
        messages: Message[] = [];
    }

    class Message {
        username: string;
        text: string;
    }

    @feature class _Chat {
        chat: Chat;
        username: string;
        @on start() {
            join(username, chat);
        }
        @on join(username, chat) {
            chat.users.push(find_user(username));
        }
        @on post(username: string, text: string) {
            chat.messages.push(new Message(username, text));
            for (let u in chat.users)  { u.display(message); }
        }
        @on display(message: Message) {
            add_to_display(html_from_message(message));
        }
    }

Then we basically have to mark functions as running on one machine or another, like this:

    server.assign([_Chat.chat, post])



    
        

_____________________________________________________________________
zerp interface thoughts:

There's actually two forms here:

.fm.ts : decorator-based feature-modular native typescript
.zero  : proper zero that translates to typescript/wasm/whatever

Processor takes .md and converts it to .fm.ts (extract code snippets).
So no code generation going on, just straight copy-paste.

Next: write the editor for those .md documents, using .md format.

Once this editor is running, then you can add a "translate to zero" button
in the interface that just uses an LLM to go either way.

This is the way :-D

Be able to write the code in either native typescript or in zero;
and use the LLM to back and forth between them. Straight translation.
So easy. Oh yeah oh yeah. That's how it will work.

So the code snippets are actually ```lang```, and there can be more than one in the same section.
They get displayed as a single snippet with a language selector.

_____________________________________________________________________
microclub interface thoughts.

- single conversation strand
- easy to post short-form posts (similar to substack)
- create side-chains

I mean really it's just a slack group, but with some nice features that promote medium-length writing (like a 2 minute read).

Write something quick for the club.

Then each one can have a side-chain conversation.

Other thought was:

people => projects. get one project up there. they make content.



_____________________________________________________________________
strategy:

1- feature modular typescript, enough to write real things with and learn.
doesn't have to be perfect, just has to work.

2- *written in fm.ts* : zerp.fm 

Just a demonstration of how that code looks in literate style.

3- once that's done: a zero-to-ts compiler, ready for wasm / wgpu backend

4- then, zerp in zero.

This is the way.

_____________________________________________________________________

_____________________________________________________________________
SUPER STUPID (but great) IDEA:

- zero can compile to c, python, or typescript
- it can borrow their syntax!

So you can do "zero.py" style:

    feature Hello:
        on hello(name: string):
            log(f"hello, {name}")
        after main():
            hello("world")

Or you can use "zero.ts" style:

    feature Hello {
        on hello(name: string) {
            log(`hello, ${name}`);
        }
        after main() {
            hello("world");
        }
    }

Or you can use "zero.cpp" style:

    feature Hello {
        on hello(string name) {
            log << "hello, " << name;
        }
        after main() {
            hello("world");
        }
    }

I think that's nice and easy, don't you? All of which means that we can do zero.ts, and write code in zero, and translate it to ts if we want to. Nice one. That way we can get it running nice and quickly in the browser, and the syntax works properly, but it's more about making it easier to get to grips with it if you're coming from one of those languages.

Do we just want to be outputting py/ts/cpp? Well, maybe, because then we can interoperate with the entire existing codebases in those languages, for free.

It's hard to know exactly where to draw that line.

_____________________________________________________________________


_____________________________________________________________________
fm.ts object system

"value types": interfaces.

Let's look at the fucking example: ideal syntax.

    feature RGBColour {
        struct Colour {
            r: number = 0;
            g: number = 0;
            b: number = 0;
        }
        on add(a: Colour, b: Colour) : Colour {
            return { r: a.r+b.r, g: a.g+b.r, b: a.b+b.r} as Colour;
        }
    }

    feature AlphaColour extends RGBColour {
        struct Colour {
            a: number = 0;
        }
        after add(a: Colour, b: Colour) : Colour {
            return extend(_result, { a: a.a + b.a })
        }
    }

So this is the thing we want to figure out.



_____________________________________________________________________
## idea of "streams

Idea is that each node in the system publishes a set of streams.
A stream is a time-stamped sequence of object values (straight JSON or binary).
"time-stamped" here means it is tagged with a global clock value.

A Node is either a single machine or a cluster of machines. The first machine in a cluster is the manager. It receives a clock from its parent and distributes it to all children.

So a cluster might look like this:

    server
    +-- asnaroo
        +-- laptop
        +-- phone
        +-- headset
        +-- drone
    +-- 8bitkick
        +-- headset
    +-- dinguskhan
        +-- desktop
        +-- laptop
        +-- phone
    +-- mrdoob
        +-- phone

However, any node can only be seen by its parent, its children, and its siblings. So if "asnaroo" asks to see the system graph, he'll see this:

    server
    +-- asnaroo
        +-- laptop
        +-- phone
        +-- headset
        +-- drone
    +-- 8bitkick
    +-- dinguskhan
    +-- mrdoob

In other words, each node can query:

    parent
    siblings
    children

Each Node type in the tree can publish a set of streams. A stream is defined by a static object type, that changes over time. For instance:

    Phone {
        pos: Gps;
        clock: Time;
        cam: Image;
        mic: Audio;
        cap: Image;
        log: Text;
    }

    Drone {
        pos: Gps;
        orientation: Angle;
        clock: Time;
        cam: Image;
        mic: Audio;
        log: Text;
        battery: number;
    }

And nodes can publish "abstract streams", such as:

    asnaroo {
        message: string;
        cam: Image;
    }

    server {
        chat: Chat;     // Chat = class { messages: string[]; }
    }

Now of course, devices can also accept commands:

    Drone {
        fly_to(pos);
        rotate_to(direction);
        take_off();
        return_to_base();
        land();
        acquire_target();
        tase_target();
    }

But those commands can only be issued by their immediate parent. So asnaroo can only control asnaroo's drone, not mrdoob's phone.

So if you take the "stream directory" for a chat session, you might see something like:

    server : chat(path)
    asnaroo : mesh, audio, text
    8bitkick : image, text

___________________________________________________________________________________
## chat example for multi-point

    class Message {
        user: string;
        text: string;
    }

    class Chat {
        title: string;
        messages: Message[];
    }

    @feature class Chat extends Main {
        @shared static chat: Chat;

        @on post(message: Message) {
            SuperChat.chat.messages.push(message);
        }

        @every(1) render() {
            display(SuperChat.chat);
        }

        @on display(chat: Chat) {
            ... generate HTML ...
        }
    }

Note a conflict issue between classes and features. We have to figure out the fucking object system. It's super annoying.




    











_____________________________________________________________________
thinking about multi-point programming

We add a new modifier/decorator `shared` that does all the heavy lifting. Here, it marks `chat` as a shared object that lives on the server, with each subscribed client's local copy kept automatically up to date.

        shared chat: Chat;

`join` calls `get_shared`, which sets the local copy of `chat` to the current state of the server's copy, and adds the client to the list of subscribers to that object.

        on async join(chatPath: string) {
            chat = await get_shared<Chat>(chatPath);
        }

Because `post` modifies a shared variable, when a client calls it, the code runs an auto-generated proxy that sends the parameters (full copies of state?) plus the fn name (`post`) to the server. The server rebroadcasts the request (including the timestamped message) to all subscribed clients (including the originator) that run the code as if it was local. The server runs the code as well, but all non-shared functions eg `update_display` compile to stubs. (needs work)

        on post(message: Message) {
            chat.messages.push(message);
        }

`onKeyPressed` is a pure client function, even though it calls a shared function.

        on keypressed(key: string) {
            if (key == 'Enter') {
                post(new Message(...));
            }
        }

And then of course, on the client, we can modify `join` and `post` to update displays:

        after join(chatPath) { initialise_display(); }
        after post(message) { update_display(message); }

        on initialise_display() { ... }
        on update_display(message: Message) { ... }

So the basic idea is:

    any function that MODIFIES a shared variable is marked "push-var"
    any function that READS a shared variable subscribes to it.

    we need to move towards this "reactive" idea.
___
think about this:

what happens if each user is a cluster of machines; they're all running the same code.
they all have to subscribe to those objects.

So this idea of "shared" = "lives on server", and "non-shared" = lives on local machine isn't quite the whole story.

It's more like each variable "lives on machine X" => "is owned by X".

So, for example, imagine that we have a laptop and a phone; the phone runs a colour selection UI.

    cluster = { laptop, phone }

    on async change_background() {
        ui = await open_colour_ui();
        
    }


    on async open_colour_ui() {
        ... code to make a colour wheel ...
        ... set up events ...
        return object
    }

    on async get_colour_from_ui(ui) {
        return ui.c
    }

_____________________________________________________________________
This idea of STREAMS though is also an interesting way to think about it.




_____________________________________________________________________
OK so. Small aside for a silly but long-returned-to application:

name: 
wltm

observation: standing around in gay pubs is boring
but apps waste too much time

can we have something in-between dating apps and the pub, please?

wltm (would like to meet) is for people who want to meet people, not waste time

super simple interface: 

- you put in a picture (face and upper body) and your top/bottomness
- we show you pictures of real people near you; if you like them, you rank them
- you tell it when you next have a half hour to kill (could be now)
- at that time, we find you the best mutual match and you video chat.
- if there's people coming online that are ranked, we let you know.
- key is: when it's time, you don't know who you're going to chat with. It's a ...
    surprise!
- variation of this works in physical spaces : "go to this pub at this time"
- "holiday mode" : I'm in town X for Y days
- "you should go to X for Y days" eg. bear week { because everyone else is }

OH MY GOD
_____________________________________________________________________
observation: scheduling microclub meetings is hard. that's the task to solve here.
that's what we'll do.

next microclub.org will be:

1- feature modular typescript IDE
2- source code editable in itself
3- runs on mobile
4- is based around a "club meeting schedule"
   (you tell it where you are and when you're free)
   also: tell it best times of day for you
5- video chat with transcript; with 
6- integrated screencast

and let's develop this concept as a framework.
Let's see what happens.

Fundamentally, you have an open structure in which you have

    Nodes   (the machines)

In this case, each Node is a user that's online and paying attention right now.
Each Node publishes one or more streams (sequence of objects at X fps).
If you need a stream, you negotiate it with the publisher, and it streams to you.

Stream types are :

    - video/audio
    - KVM
    - animated meshes
    - commands
    - document-share

If you want to run some code on a machine, you hand it the code (i.e. the features), and it runs it locally.

Each Node publishes a sort of "menu" of what it streams it accepts and can provide.

For instance: let's say you're working on your laptop, and you have a phone and a 360 camera, and a VR headset, and a drone.

Drone = accepts command/position/orientation stream, returns video/audio/gps stream
360Cam = accepts command stream, returns still / video (image stream)
VRHeadset = accepts an animated mesh, returns video/pose stream



_____________________________________________________________________
testing: I think that's a good one to look at next.
the other is: auto-logging.

I definitely want better logging happening, and I want it auto-generated.



_____________________________________________________________________
Thoughts about multi-point programming.
Let's call it "heterogenous cluster programming".

A "homogenous cluster" is an array of the same type of unit.
A "heterogenous cluster" is an array of homogenous clusters.

unit = 
    a single sequential processor
OR  a single i/o device
OR  a *cluster* : an array of units, plus comms

So for instance, a client + server is a unit in which:

unit:
    client:
        gpu[]
        cpu[]
        camera
        display
        keyboard
        mouse/trackpad
    server
        gpu[]
        cpu[]
        database
        LLM

"database" is as interesting one in that there's an idea of "permanence".

Quite like the idea of a "functional unit" = something with an input, that produces output.

    instructions + data => (cpu) => data

    request + data => (database) => data

In this way, we can think of the user as a unit as well.

    display + audio => (user) => keyboard + trackpad + mic + cam

so (keyboard, mic, trackpad, display) are "channels" carrying something
and (user, database, llm) are different "functions" that turn A into B;
they're _stateful_ things : you can send them "const-requests" that just return stuff
and don't change their state, but you can also send them "do-this" requests
that do change their state.

And of course those "functions" can be spread across multiple physical machines.

And there could be multiple users, and multiple channels. 

For instance: a single large screen viewed by 20,000 viewers. (audience), while they interact by sending messages or photographs back to the system.

let's take chat as an example:

the "chat" is the database; you're making operations on it (add message, edit, delete). 

N users, and a central object (the "chat").
We can imagine two scenarios: server, and serverless (info only exists on clients).

So there's clearly some notion of "persistence" or "centrality"; something that persists beyond a single run, versus something that's dynamic, session, or client lifespan.

So let's make those "visible" somehow: 

server.object => eg. the chat
client.object => eg. settings
client.dynamic => eg. the view interface

but remember again that we're dealing with a "network" of machines. Quite interesting to think of (for example) a drone camera, that we can command ("go to xyz/rot") and receive a video/audio stream from.

If we think about it, each "user" will be a cluster of machines, something like:

- central server
- user server
- user laptop
- user tablet
- user phone
- user headset
- 360 camera
- drone

The point is, all these machines have to collaborate to provide the final output.
Then it's just "who wants to see what".

So for instance:

    client[1].video

    client[2]: render client[1].video

So we can imagine all this happening on a single machine. We'd like this to feel the same regardless of how many users / devices per user there are.

_____________________________________________________________________
The "ideal collaborative programming interface"

1- it's time/feature organised
2- it has space for conversation, trying stuff out, notes, scribbles, as well as the final product.
3- ideally, one flows seamlessy into the other
4- AI is just a participant in this process, so it still works if it fails or underperforms

_____________________________________________________________________
Things that the framework needs:

1. a decent declaration syntax:

@feature class MyFeature extends ParentFeature

2. simple set of decorators:

    @def : define
    @on  : replace (sneak _existing)
    @after : bolt on afterwards (sneak _result)
    @before : bolt on before

3. multi-machine remote execution:

    chat example:
    clients = [..]
    server = ..

    a = func(params)                : execute locally
    a = server.func(params)         : execute on the server
    a = client[name].func(params)   : execute on a specific machine
    a = clients.func(params)        : execute on all machines (returns array)

4. proper handling of objects:

    @shared class Shared {
        @property x : number = 0;
    };

    shared.x = 5                    : broadcast to all clients

5. reactive UI, eg. documents, chat UI, that kind of thing:

    documentPanel(shared markdown);     => whenever it changes, do something.

    so we want to listen to an event coming from the outside, and do something.
