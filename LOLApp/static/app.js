window.onload = function(){
	var btn = document.getElementById("more");
	console.log(btn);
	if(btn){
		btn.addEventListener("click", function(){
		    var elements = document.getElementsByClassName("moreMatches");
		    console.log(elements);
		    for(var i=0; i < elements.length; i++){
		    	elements[i].style.display = "table-row";
		    }
		});
	}
	//react scripts
	//console.log("region: " + region + " | " + " name: " + name);
	// Get the <datalist> and <input> elements.
	var dataList = document.getElementById('champs-datalist');
	var input = document.getElementById('main-search');

	// Create a new XMLHttpRequest.
	var request = new XMLHttpRequest();

	// Handle state changes for the request.
	request.onreadystatechange = function(response) {
	  if (request.readyState === 4) {
	    if (request.status === 200) {
	      // Parse the JSON
	      var jsonOptions = JSON.parse(request.responseText);

	      // Loop over the JSON array.
	      jsonOptions.forEach(function(item) {
	        // Create a new <option> element.
	        var option = document.createElement('option');
	        // Set the value using the item in the JSON array.
	        option.value = item;
	        // Add the <option> element to the <datalist>.
	        dataList.appendChild(option);
	      });

	    } else {
	      // An error occured :(
	      input.placeholder = "Couldn't load datalist options :(";
	    }
	  }
	};

	// Set up and make the request.
	request.open('GET', '/static/champs.json', true);
	request.send();
}