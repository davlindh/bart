const { Engine } = require('json-rules-engine');
const ruleset = require('./regelfiler/regelfil_gava.json');

// Factsobjekt kan skapas med tomma värden från ruleset attributes
const facts = {};
ruleset.attributes.forEach((item) => {
    facts[item.name] = "";
});

/* Fiktiv input */
const price = 220;
const giftCode = "b1";
const giftCodesMap = { b1: "Julgåva", b2: "Jubileumsgåva", b3: "Minnesgåva", b4: "Andra gåvor" };

facts['Ges gåvan i form av pengar?'] = 'Nej';
facts['Vad är det för typ av gåva?'] = giftCodesMap[giftCode];
facts['Är gåvans marknadsvärde högre än 550 kr inklusive mervärdesskatt?'] = price > 550 ? 'Ja' : 'Nej';
facts['Ges gåvan till alla anställda alternativt en större grupp av anställda?'] = 'Ja';

const engine = new Engine();

ruleset.rules.forEach(rule => {
    engine.addRule(rule);
});

engine.on("success", (event) => {
    console.log("success: " + event.type);
});

engine.run(facts);