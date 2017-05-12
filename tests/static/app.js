window.onload = function(){
	var btn = document.getElementById("more");
	console.log(btn);
	if(btn){
		btn.addEventListener("click", function(){
		    var elements = document.getElementsByClassName("moreMatches");
		    console.log(elements);
		    for(var i=0; i < elements.length; i++){
		    	elements[i].style.display = "block";
		    }
		});
	}
}