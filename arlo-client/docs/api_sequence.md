# API Sequence

### Initial audit creation

- `POST /election/new`

- `src/components/CreateAudit.tsx` > `CreateAudit` > `onClick()` > `api()`

- `src/components/CreateAudit.tsx` > `CreateAudit` > `onClick()` > `api()`

```
{
	electionId: "03649ac0-b623-11e9-83e1-bf0244df89af"
}
```

### Initial data from /election/{electionId}/audit/status

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/index.tsx` > `AuditForms` > `updateAudit()`

- `src/components/AuditForms/index.tsx` > `AuditForms` > `updateAudit()`

```
{
  name: '',
  riskLimit: '',
  randomSeed: '',
  contests: [],
  jurisdictions: [],
  rounds: [],
}
```

### Creation of election & contests on form one

- `POST /election/{electionId}/audit/basic`

- `src/components/AuditForms/EstimateSampleSize.tsx` > `EstimateSampleSize` >
  `handlePost()` > `api()`

- `src/components/AuditForms/EstimateSampleSize.tsx` > `EstimateSampleSize` >
  `handlePost()` > `api()`

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

Getting the new status and waiting for sample size calculations to complete:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/EstimateSampleSize.tsx` > `EstimateSampleSize` >
  `handlePost()` > `poll()`

- `src/components/AuditForms/EstimateSampleSize.tsx` > `EstimateSampleSize` >
  `handlePost()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      winners: '1',
      totalBallotsCast: '2123',
    },
  ],
  jurisdictions: [],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: null,
          sampleSizeOptions: null, // null!!
        },
      ],
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: '1',
}
```

The front end will poll the back end until `sampleSizeOptions` returns something
other than `null`, like so:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/EstimateSampleSize.tsx` > `EstimateSampleSize` >
  `handlePost()` > `poll()`

- `src/components/AuditForms/EstimateSampleSize.tsx` > `EstimateSampleSize` >
  `handlePost()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      winners: '1',
      totalBallotsCast: '2123',
    },
  ],
  jurisdictions: [],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: null,
          sampleSizeOptions: [ // not null!!
            { size: 269, type: 'ASN', prob: null },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: '1',
}
```

Now the front end will show form two!

### Submitting form two

Form two has three separate POST calls.

- `POST /election/{electionId}/audit/sample-size`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `api()`

```
{
	'size': 578,
}
```

- `POST /election/{electionId}/audit/jurisdictions`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `api()`

```
{
	jurisdictions: [
		{
			id: "adams-county",
			name: "Adams County",
			contests: ["contest-1"],
			auditBoards: [
				{
					id: "63ce500e-acf0-11e9-b49e-bfb880180fb4",
					name: "Audit Board #1",
					members: []
				},
				{
					id: "7134a64e-acf0-11e9-bb0c-57b152ee1513",
					name: "Audit Board #2",
					members: []
				}
			]
		}
	]
}
```

After the first two are successfully POSTed, it GETs a new response from the
status endpoint again.

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `getStatus()`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `getStatus()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      totalBallotsCast: '2123',
      winners: '1',
    },
  ],
  jurisdictions: [ // now the jurisdictions array is populated
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
        },
      ],
      ballotManifest: { // ballotManifest is null because it hasn't been uploaded yet
        filename: null,
        numBallots: null,
        numBatches: null,
        uploadedAt: null,
      },
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: 269, // sampleSize is populated
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: null },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: '1',
}
```

Now that the front end has the `jurisdiction_id` available, it can POST the
ballot manifest:

- `POST /election/{electionId}/jurisdiction/<jurisdiction_id>/manifest`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `api()` Straight file upload
  `multipart/form-data`

And then GET the updated status:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `updateAudit()`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `updateAudit()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      winners: '1',
      totalBallotsCast: '2123',
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
          ballots: [ // there should now be a populated ballots array in each auditBoard
            {
              tabulator: '11',
              batch: '0003-04-Precinct 13 (Jonesboro Fire Department)',
              position: '313',
              status: 'AUDITED',
              vote: null,
              comment: '',
              id: '1',
            },
            ...
          ],
        },
      ],
      ballotManifest: { // ballotManifest is populated now
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: null },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: '1',
}
```

### Form Three flow

The first round of form three is displayed, and the results for one round are
posted:

- `POST /election/{electionId}/jurisdiction/<jurisdiction_id>/<round_num>/results`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `api()`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `api()`

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

The front end polls the status endpoint until every contest in the last round in
the `rounds` array has a non-null `sampleSize` value:

Incomplete sample size calculations:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `poll()`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      winners: '1',
      totalBallotsCast: '2123',
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
          ballots: [
            {
              tabulator: '11',
              batch: '0003-04-Precinct 13 (Jonesboro Fire Department)',
              position: '313',
              status: 'AUDITED',
              vote: null,
              comment: '',
              id: '1',
            },
            ...
          ],
        },
      ],
      ballotManifest: {
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: false, // audit is not finished yet
            pvalue: 0.00020431431380638307,
          },
          id: 'contest-1',
          results: { // results are populated
            'choice-1': 100,
            'choice-2': 167,
          },
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: null },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: 'Thu, 18 Jul 2019 16:59:34 GMT',
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {}, // no results for round 2 yet
          sampleSize: null, // sample size calculation hasn't been done yet
          sampleSizeOptions: null,
        },
      ],
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: '1',
}
```

Complete sample size calculations:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `poll()`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      winners: '1',
      totalBallotsCast: '2123',
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
          ballots: [
            {
              tabulator: '11',
              batch: '0003-04-Precinct 13 (Jonesboro Fire Department)',
              position: '313',
              status: 'AUDITED',
              vote: null,
              comment: '',
              id: '1',
            },
            ...
          ],
        },
      ],
      ballotManifest: {
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: false, // audit is not finished yet
            pvalue: 0.00020431431380638307,
          },
          id: 'contest-1',
          results: { // results are populated
            'choice-1': 100,
            'choice-2': 167,
          },
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: null },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: 'Thu, 18 Jul 2019 16:59:34 GMT',
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {}, // still no results for round 2 yet
          sampleSize: 379, // but now there's a sample size!
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: null },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: '1',
}
```

This cycle will continue until a round returns with
`endMeasurements.isComplete: true` on all of its contests. Which, if this
happened on the first round, would look like this:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `poll()`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      totalBallotsCast: '2123',
      winners: '1',
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
          ballots: [
            {
              tabulator: '11',
              batch: '0003-04-Precinct 13 (Jonesboro Fire Department)',
              position: '313',
              status: 'AUDITED',
              vote: null,
              comment: '',
              id: '1',
            },
            ...
          ],
        },
      ],
      ballotManifest: {
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: true, // all done!!
            pvalue: 1,
          },
          id: 'contest-1',
          results: {
            'choice-1': 100,
            'choice-2': 167,
          },
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: null },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: 'Thu, 18 Jul 2019 16:59:34 GMT',
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: '1',
}
```
