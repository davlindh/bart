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

const engine = new Engine();

ruleset.rules.forEach(rule => {
    engine.addRule(rule);
});

engine.on("success", (event) => {
    myAppActions(event.type);
});

// App specifika actions
const myAppActions = (eventType) => {

    switch (eventType) {
        case "Gåvan är skattefri":
            console.log("Action case skattefri");
            break;
        case "Gåvan är skattepliktig":
            console.log("Action case skattepliktig");
            break;
        default:
            console.log("default action");
    }
};

engine.run(facts);