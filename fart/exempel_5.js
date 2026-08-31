const { Engine } = require("json-rules-engine");

const engine = new Engine();

engine.addRule({
    // Fiktiva regler, förenklat från Kostnadsersättning - Reseräkning
    conditions: {
        all: [
            {
                fact: "Har erbetsgivaren betalat för resan?",
                operator: "equal",
                value: "Nej",
            },
            {
                fact: "Vilket transportmedel har den anställda rest med?",
                operator: "equal",
                value: "Egen bil",
            },
        ],
    },
    event: {
        type: "Skattefri ersättning kan betalas ut",
        params: {
            meddelande: "Skattefri erstättning kan betalas ut med 25kr/mil",
            milersattningdbeloppIKronor: 25,
            calc: {
                beraknaKostnadsersattningPerMil: {
                    arguments: "milersattningdbeloppIKronor,antalMil",
                    body: "return milersattningdbeloppIKronor*antalMil;",
                },
            },
        },
    },
});

const facts = {
    "Har erbetsgivaren betalat för resan?": "Nej",
    "Vilket transportmedel har den anställda rest med?": "Egen bil",
};

engine.on("success", (event) => {
    const antalMil = 20; // Antal mil som fås genom inmatning/API/mikorotjänst etc.
    const calc = event.params.calc;
    const { milersattningdbeloppIKronor } = event.params;

    // Skapar funktionen utifrån mallen i regeln
    const beraknaKostnadsersattningPerMil = new Function(
        calc.beraknaKostnadsersattningPerMil.arguments,
        calc.beraknaKostnadsersattningPerMil.body
    );

    const belopp = beraknaKostnadsersattningPerMil(
        milersattningdbeloppIKronor,
        antalMil
    );

    console.log("Beräknat belopp: " + belopp + " kr");
});

engine.run(facts);