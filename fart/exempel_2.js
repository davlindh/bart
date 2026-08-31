const { Engine } = require('json-rules-engine');
const ruleset = require('./regelfiler/regelfil_gava.json');

const facts = {
    'Ges gåvan i form av pengar?': 'Nej',
    'Vad är det för typ av gåva?': 'Julgåva',
    'Är gåvans marknadsvärde högre än 550 kr inklusive mervärdesskatt?': 'Nej',
    'Ges gåvan till alla anställda alternativt en större grupp av anställda?': 'Ja',
    'Ges gåvan i samband med att arbetsgivaren firar 25-, 50-, 75- eller 100-årsjubileum o.s.v.?': 'Nej',
    'Är gåvans marknadsvärde högre än 1 650 kr inklusive mervärdesskatt?': 'Nej',
    'Lämnas gåvan till en varaktigt anställd?': 'Ja',
    'Är gåvans marknadsvärde högre än 15 000 kr inklusive mervärdesskatt?': 'Nej',
    'Har minnesgåva redan lämnats vid ett tidigare tillfälle?': 'Nej',
    'Lämnas den nuvarande gåvan i samband med att anställningen upphör?': 'Nej',
    'Vid vilket tillfället ges gåvan?': 'Jul'
};

const engine = new Engine();

ruleset.rules.forEach(rule => {
    engine.addRule(rule);
});

const evaluate = async () => {
    const { events } = await engine.run(facts);
    // Loggar ut event-objektet för regeln
    events.map(event => console.log(event));
};

evaluate();
