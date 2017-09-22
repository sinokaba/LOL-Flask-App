//bug with compare champs and color coding
//bug download button not swithcing to instructions when clicked, js seems to be refreshing

window.onload = function(){

	modifyLayout();
	colorCodeStats();
	activateTableSorting();
	
	$("#more").on("click", function(){
		if($(this).text() == "Show More"){
			$(this).text("Show Less");
		}
		else{
			$(this).text("Show More");
		}
		$(".additional-matches").toggleClass("hidden");
	});

	$("#highlight-game-details").on("click", function(){
		var container = $('html, body');
		var link = $(document.getElementById("highlight-game-details").getAttribute("href"));
	    scrollTop: (link.offset().top - 150);
	});

	$(".pi-des").attr({
		"data-toggle": "tooltip",
		"data-placement":"bottom",
		"data-html": true,
		"title":"",
		"data-original-title": "<em>PI(Performance Index) measures a champion's performance based on cs/xp/gold leads, solo kills, objectives leads, etc compared to enemy player playing the same role</em>"
		});

	$(".wra-des").attr({
		"data-toggle": "tooltip",
		"data-placement":"bottom",
		"data-html": true,
		"title":"",
		"data-original-title": "<em>WRA(Winrate Against), the winrate of x when facing against y champion</em>"
		});

	$('[data-toggle="tooltip"]').tooltip()

	function activateTableSorting(){
    	table1 = $("#homepage-opening-tables-1").DataTable({searching: false, info: false, paging: false});
    	table2 = $("#homepage-opening-tables-2").DataTable({searching: false, info: false, paging: false});
    	table3 = $("#homepage-opening-tables-3").DataTable({searching: false, info: false, paging: false});
	}

	function destroyTables(){
    	table1.destroy();
       	table2.destroy();
    	table3.destroy();		
	}

	function get_champ_base_avg(){
	    var rawFile = new XMLHttpRequest();
	    rawFile.open("GET", file, false);
	    rawFile.onreadystatechange = function ()
	    {
	        if(rawFile.readyState === 4)
	        {
	            if(rawFile.status === 200 || rawFile.status == 0)
	            {
	                var allText = rawFile.responseText;
	                alert(allText);
	            }
	        }
	    }
	    rawFile.send(null);
	}
	//console.log("region: " + region + " | " + " name: " + name);
	// Get the <datalist> and <input> elements.
	var dataList = document.getElementById('datalist');
	var	champArray = [];
	var request = new XMLHttpRequest();

	$(".VICTORY-row").css("border-right", ".5rem solid #007E33");
	$(".DEFEAT-row").css("border-right", ".5rem solid #CC0000");
	$(".REMAKE-row").css("border-right", ".5rem solid #757575");
	// Handle state changes for the request.
	request.onreadystatechange = function(response) {
	  if (request.readyState === 4) {
	    if (request.status === 200) {
	    	var jsonOptions = JSON.parse(request.responseText);
			var champName = $("#champ-name").text()
			console.log(champName);
	      	jsonOptions.forEach(function(item) {
	      		//if(champName != item){
	      		champArray.push(item);
	        	var option = document.createElement('option');

	        	option.value = item;
		        if(dataList != null){
		       		dataList.appendChild(option);
		        }
	      		//}
	      	});
	    }
	  }
	};

	$("#import").on("click", function(){
		console.log("importingg");
		$(this).toggleClass("hidden");
		$("#items-table").toggleClass("hidden");
		$("#item-set-inst").toggleClass("hidden");
	})

	$("#return-to-items").on("click", function(){
		$("#import").toggleClass("hidden");
		$("#items-table").toggleClass("hidden");
		$("#item-set-inst").toggleClass("hidden");
	})
	// Set up and make the request.
	request.open('GET', '/static/champs.json', true);
	request.send();

	$('[data-toggle="offcanvas"]').click(function () {
		$('.row-offcanvas').toggleClass('active');
	});

	$(".role-nav-link").click(function(){
		var role = $(this).attr("id");
		console.log(role);
		$(".role-matchups").addClass("hidden");
		$("#"+role+"matchups").toggleClass("hidden");
	});

	function colorCodeStats(){
		rankPerformance("pr", 7, 1, null);
		rankPerformance("br", 1, 7, null);
		rankPerformance("champ-rating", .9, .75, 1);
		rankPerformance("player-rating", .8, .5, 1);
		rankPerformance("wr", 50.5, 49.9, null);
	};

	function rankPerformance(type, goodLimit, badLimit, greatLimit){
		vals = document.getElementsByClassName(type);
		console.log(vals);
		for(var i = 0; i < vals.length; i++){
			val = parseFloat(vals[i].innerText);
			if(type == "br"){
				if(val >= badLimit){
					vals[i].className += " below";
				}
				else if(val <= goodLimit){
					vals[i].className += " above";
				}
			}
			else{
				if(val >= goodLimit){
					if(type == "rating"){
						vals[i].className = "badge badge-primary";
					}
					else{
						vals[i].className += " above";
					}
				}
				else if(val <= badLimit){
					if(type == "rating"){
						vals[i].className = "badge badge-danger";
					}
					else{
						vals[i].className += " below";
					}
				}
				if(greatLimit != null && val >= greatLimit){
					vals[i].className += " amazing";
				}
			}
		}
	};

	//change class if window size changes
	$(window).on('resize', function() {
		modifyLayout();
	});

	function modifyLayout(){
		if($(window).width() < 768){
			$("#champ-card").removeClass("col-2");
			$("#champ-card").addClass("col");
			$("#champ-profile-cont").removeClass("col-3");
			$("#champ-profile-cont").addClass("col");
			$("#paths-container").removeClass("row");
			$(".accessories").css("width", "100%");
			$(".item-img").css("width", "100%");
			$(".champ-icon").css("width", "100%");
			$(".summ-img").css("width", "100%");
			$("#loading-col").removeClass("offset-5").addClass("offset-4")
			//$("#match-history").removeClass("table-hover").addClass("table-responsive")
			resizeBuildPaths();
		}
	    if($(window).width() >= 1024) {
	        $('#sidebar').addClass('col-6 col-md-3');
			//$("#match-history").removeClass("table-responsive").addClass("table-hover")
	    }else{
	        $('#sidebar').removeClass('col-6 col-md-3');
	    }
	};

	function resizeBuildPaths(){
		$('#skill-order-container').removeClass("col-6").addClass("row");
		$('#items-container').removeClass("col-6").addClass("row");
		$('#items-table').removeClass("col-8").addClass("col");
		$('#import-build').removeClass("col-3").addClass("col");
	};

	$(".compare").on('click', function(){
		cat = $(this).attr("id").split("-")[1];
		console.log(cat);
		compareButtonReset(cat);
	});

	function compareButtonReset(category){
		$('#add-' + category + '-input').css("border-color", "#66afe9");
		$('#compare-' + category).toggleClass("hidden");
		$('#add-' + category).toggleClass("hidden");
		$('#add-' + category + '-input').toggleClass("invisible");
		$('#add-' + category + '-input').val('');
		//toggleColSize();
	};
	/**
    $('#additionalChamp').submit(function() {
       	$.getJSON('/_compare_champs', {
        	name: $('input[name="additionalChamp"]').val()
        }, function(data) {
        	$("#result").text(data.result);
      	    $("#compare").addClass("invisible")
        });
        return false;
    });
	**/
	$('#additional-player').on('submit', function(e) {
        e.preventDefault();
        primaryPlayerInfo = $(this).attr('name').split("-");
        playerName = primaryPlayerInfo[0];
        playerRegion = primaryPlayerInfo[1];
        add_another_item("player", playerName, playerRegion);
	});

    $('#additional-champ').on('submit', function(e) {
        e.preventDefault();
        primaryChampInfo = $(this).attr('name').split("-");
        console.log(primaryChampInfo);
        champName = primaryChampInfo[0];
        champRegion = primaryChampInfo[1];
        console.log(champName + " " + champRegion);
        add_another_item("champ", champName, champRegion);
    });
	
    $("#compare-champ").on("click", function(){
		$("#add-champ-input").focus()    	
    })
	function add_another_item(category, primary_name, region){
		if(category == "champ"){
			selection = "additionalChamp"
		}
		else{
			selection = "additionalPlayer";
		}
     	var name = $('input[name=' + selection + ']').val();
     	if(checkName(name, category)){
        	$("#champs-compare-modal").modal("show")
			$('#add-'+category).toggleClass("hidden");
	 		$('#compare-'+category).toggleClass("hidden");
			$('#add-' + category + '-input').toggleClass("invisible");
			console.log($(this).attr('action') || window.location.pathname)
	        $.ajax({
	            url : $(this).attr('action') || window.location.pathname,
	            type: "GET",
	            success: function () {
	            	if(category == "champ"){
	                	getAddionalChampData(name, primary_name, region)
	                }
	               	else{
	               		getAddionalPlayerData(name, primary_name, region);
	               	}
	            },
	            error: function (jXHR, textStatus, errorThrown) {
	                console.log(errorThrown);
	            }
	        });     		

    	}
    	else{
     		compareButtonReset(category);	
    	}
	};

	function checkName(name, cat){
		if(cat == "champ"){
			if(name.length > 0 && champArray.indexOf(name) != -1){
				return true;
			}
			return false;
		}
		else{
			if(name.length > 2){
				return true;
			}
			return false;
		}
	};

    function getAddionalChampData(champ2, champ1, region){
       	$.getJSON('/_compare_champs', {
        	name: champ2,
        	region: region
        }, function(data) {
        	create_modal_compare(champ1, champ2, data.result);
        });
        return false;
    };

    $(".region").on('click', function(){
    	$("#chart-loading-bar").removeClass("hidden");
    	$("#opening-tables").addClass("hidden");
    	region = $(this).find("input").val();
    	console.log(region);
    	var d = new Date()
    	var start_time = d.getTime()/1000;
    	destroyTables();
       	$.getJSON('/_region_overall_stats', {
        	region: region
        }, function(data) {
        	$("table").find("tr:gt(0)").remove();
        	for(var i = 0; i < data.result.length; i++){
        		var rank_data = data.result[i];
        		console.log(rank_data);
        		if(i == 1){
        			console.log("players: ", rank_data, " length: ", rank_data.length);
        			var tbody = $("#top-5-players");	
					for(player in rank_data) {
						if(rank_data.hasOwnProperty(player)){
		        			var tr = $('<tr/>').appendTo(tbody);
			        		playerData = rank_data[player];
			        		console.log(playerData["rank"]);
			        		searchUrl = '<a href="' + region + '/summoner/' + player + '">';
			        		console.log(searchUrl);
				       		tr.append('<td>' + searchUrl + player + '</a></td>');
				       		if(playerData["rank"] != null){
					       		tr.append('<td>' + playerData["rank"] + '</td');
				       		}
				       		else{
					       		tr.append('<td>None</td');
					       	};
				        	tr.append('<td class="player-rating">' + playerData["player"]["rating"] + '</td>');        					
				       		tr.append('<td class="wr">' + playerData["player"]["winrate"] + '%</td>');     				
						}
					}
        		}
        		else{
	        		if(i == 0){
	        			var tbody = $("#top-5-champs")	
	        		}
	        		else{
	        			var tbody = $("#top-5-offmeta")		
	        		}
	        		for(var j = 0; j < rank_data.length; j++){
	        			champ = rank_data[j];
	        			var tr = $('<tr/>').appendTo(tbody);
	        			champSearchUrl = '<a href="' + region + '/champ/' + champ["name"] + '">';
	        			tr.append('<td>' + champ["role"] + '</td>');
	        			tr.append('<td>' + champSearchUrl + champ["name"] + '</a></td>');
		       			tr.append('<td class="champ-rating">' + champ["rating"] + '</td>');
		       			tr.append('<td class="wr">' + champ["wr"] + '%</td>');
	        		}
        		}
        	}
       		activateTableSorting();
        	colorCodeStats();
	    	$("#chart-loading-bar").addClass("hidden");
	    	$("#opening-tables").removeClass("hidden");
       		$(".region-title").text(region);
        });
	});
	
	//dynamically created bootstrap models
	function create_modal_compare(champ1Name, champ2Name, data){
		console.log(data)
		console.log(data.image)
		var $modal = $('.modal');
		var kda = Math.round(((data.rank_stats.ingame_scores.kills+data.rank_stats.ingame_scores.assists)/data.rank_stats.ingame_scores.deaths)*100)/100
		var rating = Math.round((data.rank_stats.totalRating/data.rank_stats.totalPlays)*100)/100
		var br = Math.round((data.rank_stats.totalBans/data.total_games)*1000)/10
		var pr = Math.round((data.rank_stats.totalPlays/data.total_games)*1000)/10
		var wr = Math.round((data.rank_stats.totalWins/data.rank_stats.totalPlays)*1000)/10
		var cspm = Math.round((data.rank_stats.ingame_scores.cspm/data.rank_stats.totalPlays)*100)/100
		var gpm = Math.round((data.rank_stats.ingame_scores.gpm/data.rank_stats.totalPlays)*100)/100
		var dpg = Math.round((data.rank_stats.ingame_scores.dpg/data.rank_stats.totalPlays)*100)/100
		var dmpg = Math.round((data.rank_stats.ingame_scores.dmpg/data.rank_stats.totalPlays)*100)/100
		var gpm = Math.round((data.rank_stats.ingame_scores.gpm/data.rank_stats.totalPlays)*100)/100		
		var visScore = Math.round((data.rank_stats.ingame_scores.visScore/data.rank_stats.totalPlays)*100)/100
		var objScore = Math.round((data.rank_stats.ingame_scores.objScore/data.rank_stats.totalPlays)*100)/100

		console.log(br)
		$modal.find('.modal-title').html(champ1Name + " VS " + champ2Name);
		champ_img = "http://ddragon.leagueoflegends.com/cdn/7.16.1/img/champion/"+data.image
		$("#champ2-img-name").html(
			"<img class='compare-champ-icon' src='"+champ_img+
			 "' alt='"+data.image+"'>"+champ2Name+"("+data.role1+"/"+data.role2+ ")"
			)
		$("#champ2-rating-kda").html(
			"Rating: <span class='compare-champ-rating'>"+rating+"</span> | KDA: <span class='compare-champ-kda'>"+kda+"</span>"
			)
		$("#champ2-resource").html(data.resource)
		$("#champ2-aarange").html(data.aaRange)
		$("#champ2-ms").html(data.movespeed)
		$("#champ2-br").html(br)
		$("#champ2-pr").html(pr)
		$("#champ2-wr").html(wr)
		$("#champ2-hp").html(data.hp)
		$("#champ2-hp-pl").html(data.hpPL)
		$("#champ2-hpregen").html(data.hpRegen)
		$("#champ2-hpregen-pl").html(data.hpRegenPL)
		$("#champ2-armor").html(data.armor)
		$("#champ2-armor-pl").html(data.armorPL)
		$("#champ2-mr").html(data.mr)
		$("#champ2-mrPL").html(data.mrPL)
		$("#champ2-ad").html(data.ad)
		$("#champ2-ad-pl").html(data.adPL)
		$("#champ2-attackspeed").html(data.attackspeed)
		$("#champ2-attackspeed-pl").html(data.attackspeedPL + "%")

		if(data.resource == "Mana"){
			$("#champ2-mana").html(data.mana)
			$("#champ2-mana-pl").html(data.manaPL)
			$("#champ2-manaregen").html(data.manaRegen)
			$("#champ2-manaregen-pl").html(data.manaregenPL)
		}
		$("#champ2-dpg").html(dpg)
		$("#champ2-dmpg").html(dmpg)
		$("#champ2-gpm").html(gpm)
		$("#champ2-vis").html(visScore)
		$("#champ2-objectives").html(objScore)
		$("#champ2-cspm").html(cspm)

		compare_champ_values("compare-champ1-rank-stats", 2, false);
		compare_champ_values("compare-champ1-base", 3, true);
		compare_champ_values("compare-champ2-static", 3, true, "static-base");

		champsRating = document.getElementsByClassName("compare-champ-rating");
		champ1Rating = champsRating[0].innerText;
		champ2Rating = champsRating[1].innerText;
		if(champ1Rating > champ2Rating){
			champsRating[0].className += " above";
			champsRating[1].className += " below";
		}
		else if(champ2Rating > champ1Rating){
			champsRating[1].className += " above";
			champsRating[0].className += " below";			
		}
		champsKda = document.getElementsByClassName("compare-champ-kda");
		champ1Kda = champsKda[0].innerText;
		champ2Kda = champsKda[1].innerText;		
		if(champ1Kda > champ2Kda){
			champsKda[0].className += " above";
			champsKda[1].className += " below";
		}
		else if(champ2Kda > champ1Kda){
			champsKda[1].className += " above";
			champsKda[0].className += " below";			
		}
		console.log(champ1Rating + " " + champ2Rating + " " + champ1Kda + " " + champ2Kda);
		$modal.find('.modal-body').toggleClass("hidden")
	};

	function compare_champ_values(table1Name, stopIndex, tbody, extraArgs=null){
		var tableD = document.getElementById(table1Name);
		if(tbody){
			var tbody = tableD.getElementsByTagName("tbody")[0];
			var tableRows = tbody.getElementsByTagName("tr");
		}
		else{
			var tableRows = tableD.getElementsByTagName("tr");
		}
		console.log(tableRows);
		if(extraArgs == null){
			startIndex = 1;
		}
		else{
			startIndex = 0;
		}
		for(var i=0; i<tableRows.length; i++){
			for(var j=startIndex; j<stopIndex; j++){
			    var tdClassName = tableRows[i].getElementsByTagName("td")[j].className.split(" ")[0];
			    var stats = document.getElementsByClassName(tdClassName);
			    var champ1Stat = stats[0];
			    var champ2Stat = stats[1];
			    var champ1StatClassName = champ1Stat.className;
			    var champ2StatClassName = champ2Stat.className;	
			    if(extraArgs != null){
			    	var champ1StatVal = champ1Stat.innerText.split(":")[1];
			    	var champ2StatVal = champ2Stat.innerText.split(":")[1];
			    	if(champ1StatVal.indexOf("%") != -1){
			    		champ1StatVal = champ1StatVal.split("%")[0];
			    		champ2StatVal = champ2StatVal.split("%")[0];
			    	}
			    }
			    else{
			    	var champ1StatVal = champ1Stat.innerHTML;
			    	var champ2StatVal = champ2Stat.innerHTML;
			    }
			    if(!isNaN(champ1StatVal)){
				    if(champ1StatClassName.indexOf("mana") != -1){
				    	if($("#champ2-resource").text() == "Mana" && $("#champ1-resource").text() == "Mana"){
						    console.log(stats);
						    if(parseVal(champ1StatVal) > parseVal(champ2StatVal)){
						    	console.log(parseVal(champ1StatVal) + " > " + parseVal(champ2StatVal));
						    	champ1Stat.className += " above";
						    	champ2Stat.className += " below";
						    }
						    else if(parseVal(champ1StatVal) < parseVal(champ2StatVal)){
						    	console.log(parseVal(champ1StatVal) + " < " + parseVal(champ2StatVal));
						    	champ1Stat.className += " below";
						    	champ2Stat.className += " above";
						    }
				    	}
				    }
				    else{		    
					    console.log(stats);
					    if(parseVal(champ1StatVal) > parseVal(champ2StatVal)){
					    	console.log(parseVal(champ1StatVal) + " > " + parseVal(champ2StatVal));
					    	champ1Stat.className += " above";
					    	champ2Stat.className += " below";
					    }
					    else if(parseVal(champ1StatVal) < parseVal(champ2StatVal)){
					    	console.log(parseVal(champ1StatVal) + " < " + parseVal(champ2StatVal));
					    	champ1Stat.className += " below";
					    	champ2Stat.className += " above";
					    }
					}
			    }
			}
		}
	}
	function parseVal(val){
		if(Number(val)){
			if(val % 1 === 0){
				return parseInt(val);
			}
			return val;
		}
		return val;
	}

	var $modal = $('.modal');

	$modal.on('show.bs.modal', function(e) {
		$(this).addClass('modal-scrollfix').find('.modal-title').html('<h1>loading...</h1>');
	});

	$modal.on('hide.bs.modal', function(e) {
		$(this).find('.modal-body').toggleClass("hidden");
	});
}