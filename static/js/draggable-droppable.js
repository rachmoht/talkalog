// draggable and droppable for upload to collection traversal
$(function() {
    var draggable = $( ".draggable" );
    draggable =  _.isArray(draggable) ?
        draggable : [draggable];
    _.each(draggable, function(item){
        item.draggable({ 
            helper: "original",
            revert: "invalid",
            stack: ".draggable",

        });
    })
    
    var droppable = $( ".droppable");
    droppable = _.isArray(droppable) ?
        droppable : [droppable];

    _.each(droppable, function(item){
        item.droppable({
            drop: function (event, ui){
                var uploadId = ui.draggable.attr('upload-id');
                console.log('Upload ID: ' + uploadId);

                var collectionId = event.target.attributes['collection-id'].value;
                console.log('Collection ID: ' + collectionId);

                $.ajax({
                    url: "/add-to-collection/"+uploadId +"",
                    type: "POST",
                    data: {
                        'upload_id': uploadId,
                        'collection_id': collectionId 
                    } 
                }).done(function(data) {
                    window.location.href = "/success-collection?UPLOAD_ID="+uploadId+"&COLLECTION_ID="+collectionId;
                });
            }
        });
    })
});