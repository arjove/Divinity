# Catchynaam
## API-request
{
	lastLocations: [{
	'Alpha',
	[52.23422, 6.828228],
	'+2 2018-23-23 00:00:00
	}]
}

Tristan implementeert: 
incrementVisitCount {
	
}
Tristan maakt een tabelletje aan.


## Groepenvolgorde
Manual bookkeeping

Snelste route tussen groepen die 0 keer bezocht zijn. 

Complete graaf tussen verschillende groepgebieden. 
Vanaf huidige locatie naar dichtsbijzijnde groepen.
Voor maximaal 3 groepen.

## Routezoekding
// Google API
Optioneel walking speed (optimistic/normal) voor vossen meegeven in de apicall naar google.
Walking directions
Laatst bekende locatie (hint/hunt) + scoutinggroep
--> Lijst van 3 routes.
--> [{
	'Kwekerijweg',
	'300m',
	'6min',
	'rechtsaf'
}, ...]
--> Huidige positie = looptijd van wegen tot de tijd matcht met de huidige tijd.
-->  return alle locaties (+ route naar dichtsbijzijnde scoutinggroep) in volgorde van kortste route (lat, lng, naam weg).

2 a 3 routes voor de meest waarschijnlijke scoutinggroep 
+ 1 voor de op een na meest waarschijnlijke scoutinggroep

Tristan: google api key

6 * 1 = 6

Cachen (eens per 30 seconden)

12 * 6 * 24
## URL app aanpassen + gps tracker verder repareren?


## 
