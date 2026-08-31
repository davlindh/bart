const { Engine } = require('json-rules-engine');
const ruleset = require('./regelfiler/regelfil_gava.json');

// Factsobjekt kan skapas med tomma värden från ruleset attributes
const facts = {};
ruleset.attributes.forEach((item) => {
    facts[item.name] = "";
});

facts['Ges gåvan i form av pengar?'] = 'Nej';
facts['Vad är det för typ av gåva?'] = 'Julgåva';
facts['Är gåvans marknadsvärde högre än 550 kr inklusive mervärdesskatt?'] = 'Nej';
facts['Ges gåvan till alla anställda alternativt en större grupp av anställda?'] = 'Ja';

// Lägger till en funktion för regeln som har index 3
ruleset.rules[3].event.params.f = () => {
    const a = 8;
    const b = 8;
    console.log("Exempel på en App-specifik funtion, " + a + " * " + b + " = ", a * b)
};

const engine = new Engine();

ruleset.rules.forEach(rule => {
    engine.addRule(rule);
});

engine.on("success", (event) => {
    // Exekvera funktionen för regeln
    if (event.params.f) event.params.f();
});

engine.on("failure", () => {
    console.log("Facts matchade inte regel");
});

const evaluate = async () => {
    const { events } = await engine.run(facts);
    if (events.length === 0) console.log("Inputdata matchade ingen regel");
    else console.log("Antal regler som matchades: " + events.length);
};

evaluate();