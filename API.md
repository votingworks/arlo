# API Documentation

JSON for sure.

- `GET /audit/status` -- get the whole data structure for the whole audit

```
{
	name: "Primary 2019",
	riskLimit: 10,
	randomSeed: "sdfkjsdflskjfd",

	contests: [
	    {
			id: "contest-1",
			name: "Contest 1",
			
			choices: [
				{
					name: "Candidate 1",
					numVotes: 42
				}
			],
			
			totalBallotsCast: 4200
		}
	],
	
	jurisdictions: [
		{
			id: "adams-county",
			name: "Adams County",
			contests: ["contest-1"],
			auditBoards: [
				{
					id: "audit-board-1",
					members: []
				},
				{
					id: "audit-board-2",
					members: []
				}
			],
			ballotManifest: {
				filename: "Adams_County_Manifest.csv"
				numBallots: 123456,
				numBatches: 560,
				uploadedAt: "2019-06-17 11:45:00"
			}
		}
	],
	
	rounds: [
		{
			startedAt: "2019-06-17 11:45:00",
			endedAt: "2019-06-17 11:55:00",
			contests: [
				{
					id: "contest-1",
					endMeasurements: {
						risk: 11,
						pvalue: 0.085,
						isComplete: false
					},
					results: {
						"candidate-1": 55,
						"candidate-2": 35
					},
					minSampleSize: 55,
					chosenSampleSize: 66
				}
			],
			jurisdictions: {
				"adams-county": {
					numBallots: 15,
				}
			}
		}
	]
		
}
```

- `POST /audit/basic` -- the overall audit configuration

```
{
	name: "Primary 2019",
	riskLimit: 10,
	randomSeed: "sdfkjsdflskjfd",

	contests: [
	    {
			id: "contest-1",
			name: "Contest 1",
			
			choices: [
				{
					id: "candidate-1",
					name: "Candidate 1",
					numVotes: 42
				}
			],
			
			totalBallotsCast: 4200
		}
	]
}
```


- `POST /audit/jurisdictions` -- the jurisdictions that are going to be auditing

```
{
	jurisdictions: [
		{
			id: "adams-county",
			name: "Adams County",
			contests: ["contest-1"],
			auditBoards: [
				{
					id: "audit-board-1",
					members: []
				},
				{
					id: "audit-board-2",
					members: []
				}
			]
		}
	]
}
```

- `POST /audit/sample-sizes` -- the desired sample sizes for round 1

```
{
	contests: [
	    {
			id: "contest-1",
			chosenSampleSize: 66
		}
	]
}
```

- `POST /jurisdiction/<jurisdiction_id>/manifest` -- the ballot manifest

straight file upload `multipart/form-data`


- `DELETE /jurisdiction/<jurisdiction_id>/manifest` -- delete the ballot manifest

- `POST /jurisdiction/<jurisdiction_id>/<round_id>/results` -- the results for one round

```
{
	"contests": [
		{
			id: "contest-1",
   			results: {
				"candidate-1": 55,
				"candidate-2": 35
			}
		}
	]
}
```

- `GET /jurisdiction/<jurisdiction_id>/<round_id>/retrieval-list` -- retrieval list as an attachment

- `GET /audit/report` -- the audit report
