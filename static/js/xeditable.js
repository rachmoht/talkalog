// inline editing via x-editable + bootstrap
$(function(){
    $('.edit').click(function(e){  
        var uploadId = $(this).siblings('.upload-title').attr(
            'upload-id');
        console.log('the id to edit: ' + uploadId);

        $('#upload-' + uploadId).editable({
            url: '/edit/title/' + uploadId,
            title: 'Edit Title',
            pk: 1,
            toggle: 'manual',
            params: function(params) {
                var data = {};
                data['id'] = params.pk;
                data['name'] = params.value;
                return data;
            }
        });

        e.stopPropagation();
        $('#upload-' +  uploadId).editable('toggle');
    });
});