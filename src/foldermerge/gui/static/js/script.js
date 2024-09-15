//const my_import = require('https://code.jquery.com/jquery-3.2.1.min.js');

var isMouseDown = false;

const files_data = {
	"1754618168168731" : {
	 "source_path" : "C:/untruc",
	 "display" : "untruc",
	 "type" : "file",
	 "parent" : "1843541387354",
	 "showed" : true
	},
	"75727827417" : {
	 "source_path" : "C:/pastruc",
	 "display" : "pastruc",
	 "type" : "file",
	 "parent" : "1843541387354",
		"showed" : true
	},
	"453785781278" : {
	 "source_path" : "C:/deuxtruc",
	 "display" : "deuxtruc",
	 "type" : "file",
	 "parent" : "1843541387354",
		"showed" : true
	},
	"12376827827" : {
	 "source_path" : "C:/blabliblou/microute",
	 "display" : "microute",
	 "type" : "file",
	 "parent" : "0716516843",
		"showed" : true
	},
	"784278978278" : {
	 "source_path" : "C:/blabliblou/chantruc",
	 "display" : "chantruc",
	 "type" : "file",
	 "parent" : "0716516843",
		"showed" : true
	}
};

const folder_data = {
	"1843541387354": {
	 "source_path" : "C:/",
	 "display" : "C:/",
	 "type" : "folder",
	 "parent" : null
	},
	"0716516843": {
	 "source_path" : "C:/blabliblou",
	 "display" : "blabliblou",
	 "type" : "folder",
	 "parent" : "1843541387354"
	}
}

const selected_items = new Set();

// render_files();

//$(document).ready(render_files);

document.addEventListener("DOMContentLoaded", render_files);

var root_parent = null;

console.log("Root parent :");
console.log(root_parent);

function get_folder_div(object_id){
	console.log("Getting or creating parent div for :");
	console.log(object_id);
	if (object_id === null){
		return root_parent;
	} 
	console.log("object was not null");
	var folder_div = document.getElementById(object_id);
	if (folder_div === null){
		folder_div = create_folder_div(object_id);
	} 
	return folder_div;
}

function create_folder_header(folder_div){
	let row = document.createElement('div');
	row.className = "row-container list-headers";
	folder_div.appendChild(row);
	
	let checkbox = document.createElement('div');
	checkbox.className = "element";
	checkbox.innerHTML = "Select";
	row.appendChild(checkbox);
	
	let expand_elem = document.createElement('div');
	expand_elem.className = "element expand";
	row.appendChild(expand_elem);
	
	let paths_elem = document.createElement('div');
	paths_elem.className = "element";
	paths_elem.innerHTML = "Paths";
	row.appendChild(paths_elem);
	
	let second_expand_elem = document.createElement('div');
	second_expand_elem.className = "element expand";
	row.appendChild(second_expand_elem);
	
	let actions_elem = document.createElement('div');
	actions_elem.className = "element";
	actions_elem.innerHTML = "Actions";
	row.appendChild(actions_elem);
	
	let third_expan_elem = document.createElement('div');
	third_expan_elem.className = "element expand afteractions";
	row.appendChild(third_expan_elem);
}

function create_folder_div(object_id){
	let folder_object = folder_data[object_id];
	console.log("Parent of object is :");
	console.log(folder_object["parent"]);
	let parent_folder_div = get_folder_div(folder_object["parent"]);
	
	console.log("Creating folder div from object id :");
	console.log(object_id);
    console.log(parent_folder_div);

	folder_div = document.createElement('div');
	folder_div.className = "list-container";
	folder_div.id = object_id;
	parent_folder_div.appendChild(folder_div);
	
	var title = document.createElement('div');
	title.className = "list-title";
	title.innerHTML = folder_object["display"];
	folder_div.appendChild(title);
	
	create_folder_header(folder_div);
	return folder_div;
}

function create_file(file_id){
	var file = files_data[file_id];
	var folder_div = get_folder_div(file["parent"]);
	
	var row = document.createElement('div');
	row.className = "row-container filter-item";
	row.id = file_id
	folder_div.appendChild(row);
	
	var checkbox = document.createElement('div');
	checkbox.className = "element checkable";
	checkbox.addEventListener('mouseenter', selects_item);
    checkbox.addEventListener('mousedown', selects_item);
	row.appendChild(checkbox);
	
	var checkbox_input = document.createElement('input');
	checkbox_input.type = "checkbox";
	checkbox_input.addEventListener('click', function(event) {
        event.preventDefault();
    });
	checkbox.appendChild(checkbox_input);
	
	var separator = document.createElement('div');
	separator.className = "element expand beforepath";
	row.appendChild(separator);
		
	var description = document.createElement('div');
	description.className = "element text-description";
	description.innerHTML = file["display"];
	row.appendChild(description);
	
	var separator = document.createElement('div');
	separator.className = "element expand";
	row.appendChild(separator);
	
	var copy_button = document.createElement('div');
	copy_button.className = "element action-button";
	copy_button.innerHTML = "Copy to reference";
	row.appendChild(copy_button);
	
	var delete_button = document.createElement('div');
	delete_button.className = "element action-button";
	delete_button.innerHTML = "Delete";
	row.appendChild(delete_button);
}

function render_files(){

	window.root_parent = document.getElementById("filter-container");

	for (var file_id in files_data){
		create_file(file_id);
	}
};

// $(document).mousedown(function() {
// 	isMouseDown = true;
// }).mouseup(function() {
// 	isMouseDown = false;
// 	$('body').removeClass('noselect');
// });

document.addEventListener('mousedown', function() {
	isMouseDown = true;
});

document.addEventListener('mouseup', function() {
	isMouseDown = false;
	document.body.classList.remove('noselect');
});
  

document.querySelectorAll('.element.checkable').forEach(function(element) {
	element.addEventListener('mouseenter', selects_item);
	element.addEventListener('mousedown', selects_item);
});

document.querySelectorAll('.element.checkable input[type="checkbox"]').forEach(function(checkbox) {
	checkbox.addEventListener('click', function(event) {
		event.preventDefault();
	});
});

var filterTextarea = document.querySelector('#filter-command textarea');
if (filterTextarea) {
  filterTextarea.addEventListener('focusout', filter_divs);
  filterTextarea.addEventListener('keypress', function(e) {
    if (e.which === 13) {
      e.preventDefault();
      console.log(this);
      filter_divs(this);
    }
  });
}


// $('.element.checkable').mouseenter(selects_item);
// $('.element.checkable').mousedown(selects_item);
// $('.element.checkable input[type="checkbox"]').click(function(event) {
//   event.preventDefault();  
// });

// $('#filter-command textarea').focusout(filter_divs);
// $('#filter-command textarea').on('keypress', function(e) {
//     if (e.which === 13) { // 13 is the enter key
//         e.preventDefault(); // Prevent the default action (new line)
// 			  console.log(this);
//         filter_divs(this);
//     }
// });

function selects_item(item) {
	//console.log(item);
	
	if (item.type == "mouseenter") {
		if (!isMouseDown) {
			return;
		} else {
			document.body.classList.add('noselect');
		}
	}
	
	var parent = item.currentTarget.parentElement;
	console.log(parent);
	if (parent.classList.contains('selected')) {
		parent.classList.remove('selected');
		parent.querySelector('div.checkable input').checked = false;
		if (selected_items.has(parent.getAttribute('id'))) {
			selected_items.delete(parent.getAttribute('id'));
		}
	} else {
		parent.classList.add('selected');
		parent.querySelector('div.checkable input').checked = true;
		selected_items.add(parent.getAttribute('id'));
	}

}


function act_on_selection(event){
	console.log(selected_items);
}


function filter_divs(item) {
	console.log(item);
    let filter;
    if (item.target) {
        filter = item.target.value;
    } else {
        filter = item.value;
    }
	console.log("Variable filter is : " +  filter);
	if (filter){
		
		for (let file_id in files_data) {
			var file_div = document.getElementById(file_id);
			if ( files_data[file_id]["source_path"].includes(filter) ) {
				file_div.classList.remove('hidden');
				files_data[file_id]["showed"] = true;
			}
			else {
				file_div.classList.add('hidden');
				files_data[file_id]["showed"] = false;
			}
		}
		
		for (let folder_id in folder_data) {
			var folder_div = document.getElementById(folder_id);
			console.log(folder_div);
			if (check_folders_vilibility(folder_id)) {
				folder_div.classList.remove('hidden');
			}
			else {
				folder_div.classList.add('hidden');
			}
		}
	}
	
	else {
		
		for (var file_id in files_data) {
			var file_div = document.getElementById(file_id);
			file_div.classList.remove('hidden');
			files_data[file_id]["showed"] = true;
		}
		
		for (let folder_id in folder_data) {
			var folder_div = document.getElementById(folder_id);
			folder_div.classList.remove('hidden');
		}
	}
};

function check_files_visibility(parent_id) {
  for (let file_id in files_data) {
    let file = files_data[file_id];
    if (file["parent"] === parent_id && file["showed"] !== false) {
      return true;
    }
  }
  return false;
}

function check_folders_vilibility(parent_id){
	if (check_files_visibility(parent_id)){
		return true;
	}
	for (let folder_id in folder_data) {
		let folder = folder_data[folder_id];
		if (folder["parent"] === parent_id && check_folders_vilibility(folder_id)) {
			return true;
		}
	}
	return false;
}
