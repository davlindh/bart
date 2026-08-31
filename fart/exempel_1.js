const { Engine } = require('json-rules-engine');

// En regel för om Fordon är Bil. Event Type är en sträng som förklarar vad ersättningen blir.
const rule =
{
    conditions: {
        all: [{
            fact: "Fordon?",
            operator: "equal",
            value: "Bil",
        }]
    },
    event: {
        type: "Ersättning utgår med 18,5 kr/mil"
    }
};

// Skapa en engine-instans och lägg till regeln 
const engine = new Engine();
engine.addRule(rule);

// Fact-objektet är här hårdkodat men motsvarar annars dynamisk inputdata
const facts = {
    'Fordon?': 'Bil',
};

const evaluate = async () => {
    // Kör regelmotorn med Facts-objektet
    const { events } = await engine.run(facts);
    events.forEach(event => console.log("Utfall: " + event.type));
    // I konsolen: "Utfall: Ersättning utgår med 18,5 kr/mil" 
};

evaluate();
