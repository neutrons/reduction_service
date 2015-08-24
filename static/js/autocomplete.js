/**
 * Some Variables
 */

var NON_VALID_EXPERIMENT_ID = 'uncategorized';


/**
 * Populates the autocomplete for data for runs
 * for a certain experiment_id
 *  
 */
function set_autocomplete_run_fields(run_selector,experiment_id_selector) {
    if  ( is_valid_experiment(experiment_id_selector) ) {
    	runs_jsonurl = get_all_runs_json_url($(experiment_id_selector).val());
        set_autocomplete_ranged(selector,runs_jsonurl);
    }
};


/**
 * Populates the autocomplete for an experiment field
 */
function set_autocomplete_experiment_field(experiment_id_selector){
	var jsonurl = get_all_experiments_json_url();
    if  ($(experiment_id_selector).is('*')) { // if the selector exists:
        set_autocomplete(experiment_id_selector,jsonurl);
    }
}

/**
 * Re-populates the autocomplete for data for runs when the experiment field
 * is changed!
 * Loaded at startup.
 * Example:  update_autocomplete_runs_when_experiment_changes("#id_vanadium_runs,[id$='data_runs']","#id_experiment");
 */    
function update_autocomplete_runs_when_experiment_changes(run_selector,experiment_id_selector) {
    $(experiment_id_selector).on( "autocompletechange", function(event,ui) {
   		var runs_jsonurl = get_all_runs_json_url($(experiment_id_selector).val());
        set_autocomplete_ranged(run_selector,runs_jsonurl);
	});
};






/**
 * is_valid_experiment
 * 
 * Example: is_valid_experiment('#id_experiment')
 * 
 * @param selector
 * @returns {Boolean}
 */

function is_valid_experiment(selector){
	if ($(selector).is('*') && $(selector).val().length > 0 && $(selector).val().toLowerCase() != NON_VALID_EXPERIMENT_ID)
		return true
	else
		return false
}


/*******************************************************************************
 * Function to populate the autocomplete from a remote json. This is used on a
 * field that needs a single run number!
 */
function set_autocomplete(selector, jsonurl) {
	$.ajax({
		url : jsonurl,
		type : 'get',
		dataType : 'json',
		async : true,
		success : function(data) {
			// console.log(data);
			$(selector).autocomplete({
				source : data,
				minLength : 0,
				// fires the change event on selection!
				select : function(event, ui) {
					this.value = ui.item.value;
					$(this).trigger('change');
					return false;
				},
			}).bind('focus', function() {
				if (!$(this).val().trim()) {
					$(this).keydown();
				}
			});
		},
	});
}

/*************************************************************
 * 
 * Set of functions to to populate the autocomplete from a remote json. For
 * ranged fields, .e.g,: 4588-4590,465-658
 */

function set_autocomplete_ranged(selector, jsonurl) {
	$.ajax({
		url : jsonurl,
		type : 'get',
		dataType : 'json',
		async : true,
		success : function(data) {
			$(selector).autocomplete(
					{
						minLength : 0,
						source : function(request, response) {
							response($.ui.autocomplete.filter(data,
									extractLast(request.term)));
						},
						focus : function() {
							return false;
						},
						select : function(event, ui) {
							// If there's more than a single item
							if (this.value.search(/[,-]\s*/) >= 0) {
								var terms_all = separate(this.value);
								var terms = terms_all[0];
								var delimiters = terms_all[1];
								// remove the current input
								if (this.value.substr(-1) != ","
										&& this.value.substr(-1) != "-") {
									terms.pop();
								}
								// add the selected item
								terms.push(ui.item.value);
								this.value = join(terms, delimiters);
							} else {
								this.value = ui.item.value;
							}
							$(this).trigger('change');
							return false;
						}
					}).bind('focus', function() {
				if (!$(this).val().trim())
					$(this).keydown();
			});
		}
	});
}
function split(val) {
	return val.split(/[,-]\s*/);
}
function extractLast(term) {
	return split(term).pop();
}
function remove_empty_string_from_array(array) {
	for (var i = array.length - 1; i >= 0; i--) {
		if (array[i] === '') {
			array.splice(i, 1);
		}
	}
}
function separate(val) {
	var values = val.split(/[,-]\s*/);
	var delimiters = val.split(/[^,-\s]/);
	remove_empty_string_from_array(values);
	remove_empty_string_from_array(delimiters);
	return [ values, delimiters ];
}
function join(values, delimiters) {
	out = "";
	for (i = 0; i < delimiters.length; i += 1) {
		out += values[i] + delimiters[i];
	}
	out += values[i];
	return out;
}


/**
 * Jquery autcomplete dialog
 * It will open a jquery modal dialog to look for a run
 * given an experiment
 * 
 * Must be called from a button, like:
 * <button id="run-lookup" onclick="run_lookup('{{config_form.vanadium_runs.id_for_label}}'); return false;">Vanadium Lookup</button>
 */
function run_lookup(caller) {
	
	
	if ( !$('#dialog-run-lookup').is('*')) { // if the selector does not exists:
	    $("body").append('\
	    <div id="dialog-run-lookup" title="Run Lookup">\
		  <form>\
		  	<table>\
		  	  <tr>\
		      <th><label for="dialog-ipts">Experiment</label></th>\
		      <td class="long_input"><input type="text" name="ipts" id="dialog-ipts" class="ui-widget-content ui-corner-all"></td>\
		      </tr><tr>\
		      <th><label for="dialog-run">Run</label></th>\
		      <td class="long_input"><input type="text" name="run" id="dialog-run" class="ui-widget-content ui-corner-all"></td>\
		      </tr>\
		    </table>\
		      <input type="submit" tabindex="-1" style="position:absolute; top:-1000px">\
		  </form>\
		</div>');
	    
	    set_autocomplete_experiment_field('#dialog-ipts');
	    update_autocomplete_runs_when_experiment_changes("#dialog-run","#dialog-ipts");
	}
	
    $("#dialog-run-lookup").dialog({
            title: "Run lookup",
            resizable: true,
			width:'auto',
			modal: true,
            
			close: function(event, ui) {
                //$("#dialog-run-lookup").remove();
                $( this ).dialog( "close" );
            },
	      	buttons: {
	          "OK": function() {
	          	var run = $('#dialog-run').val();
	          	console.log($('#dialog-ipts').val() + ' -> ' + run);
	          	
	          	$('#'+caller).val($('#'+caller).val()+run);
	          	
	          	console.log($('#'+caller).val() + ' + ' + run);
	          	
	            
				$("#dialog-run").val('');
	            $( this ).dialog( "close" );
	          },
	          Cancel: function() {
	            $( this ).dialog( "close" );
	          }
	      	},
        });
    return true;
};
//$(function() {
//    $("#dialog-run-lookup").hide();
//});


