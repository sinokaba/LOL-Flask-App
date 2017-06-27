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

	//console.log("region: " + region + " | " + " name: " + name);
	// Get the <datalist> and <input> elements.
	var navDataList = document.getElementById('nav-datalist');
	var mainDataList = document.getElementById('main-datalist');
	var mainInput = document.getElementById('main-search');
	var navInput = document.getElementById('nav-search');

	var request = new XMLHttpRequest();

	// Handle state changes for the request.
	request.onreadystatechange = function(response) {
	  if (request.readyState === 4) {
	    if (request.status === 200) {
	      var jsonOptions = JSON.parse(request.responseText);

	      jsonOptions.forEach(function(item) {
	        var option = document.createElement('option');

	        option.value = item;

	        if(navDataList != null){
	       		navDataList.appendChild(option);
	        }
	        else if(mainDataList != null){
	       		mainDataList.appendChild(option);
	        }
	      });
	    } else {
	      mainInput.placeholder = "Couldn't load datalist options :(";
	      navInput.placeholder = "Couldn't load datalist options :(";
	    }
	  }
	};

	// Set up and make the request.
	request.open('GET', '/static/champs.json', true);
	request.send();

	$('[data-toggle="offcanvas"]').click(function () {
		$('.row-offcanvas').toggleClass('active')
	});
}