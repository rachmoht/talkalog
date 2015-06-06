// Folder toggle functionality 
function toggleFolder(e) {
    $(e.target)
        .prev('.panel-heading')
        .find('span.indicator')
        .toggleClass('glyphicon-folder-close glyphicon-folder-open');
}
$('#accordion').on('hidden.bs.collapse', toggleFolder);
$('#accordion').on('shown.bs.collapse', toggleFolder);