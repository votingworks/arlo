document
  .getElementById("downloadResultsButton")
  .addEventListener("click", async () => {
    try {
      const response = await fetch(
        "https://results.sos.ga.gov/cdn/results/Georgia/export-2024NovGen.json"
      );
      if (!response.ok) throw new Error("Network response was not ok");

      const jsonData = await response.json();
      const rows = transformData(jsonData);
      createAndDownloadCSV(rows);
    } catch (error) {
      console.error("Error fetching or processing JSON:", error);
      alert("Failed to fetch or process the data.");
    }
  });

// Transform data from json to rows
function transformData(jsonData) {
  const rows = [];

  const localResults = jsonData.localResults;
  localResults.forEach((jurisdiction) => {
    const row = {
      Jurisdiction: jurisdiction.name.replace(" County", ""),
      "Donald J. Trump (Rep) - SoS Results": 0,
      "Kamala D. Harris (Dem) - SoS Results": 0,
      "Chase Oliver (Lib) - SoS Results": 0,
      "Jill Stein (Grn) - SoS Results": 0,
    };

    const ballotItems = jurisdiction.ballotItems;
    const presidentialItem = ballotItems[0];
    const presidentialOptions = presidentialItem.ballotOptions;
    presidentialOptions.forEach((option) => {
      row[option.name + " - SoS Results"] = option.voteCount;
    });

    rows.push(row);
  });

  // Sort rows by Jurisdiction name
  rows.sort((a, b) => a.Jurisdiction.localeCompare(b.Jurisdiction));

  const totalResults = jsonData.results;
  const presidentialTotal = totalResults.ballotItems[0];
  const presidentialTotalOptions = presidentialTotal.ballotOptions;
  const totalRow = {
    Jurisdiction: "Total",
  };
  presidentialTotalOptions.forEach((option) => {
    totalRow[option.name + " - SoS Results"] = option.voteCount;
  });

  rows.push(totalRow);
  return rows;
}

// Create and download CSV
function createAndDownloadCSV(rows) {
  const csvContent = Papa.unparse({
    data: rows,
  });

  const blob = new Blob([csvContent], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "GA_presidential_results_nov_2024.csv";
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
