
function durationFieldOnValueChange(self) {
    try {
        // calculating needed variables
        var id_prefix = self.id.substr(0, self.id.length - 1);
        var current_index = self.id.substr(-1);
        var target_index = current_index == '0' ? '1' : '0';
        var target_id = id_prefix + target_index;
        var target_obj = $('#' + target_id);
        var self_obj = $(self);

        // if this duration field is not required, abort
        if (target_obj.attr('required') == undefined && self_obj.attr('required') == undefined) {
            return;
        }

        // if self has no value but target has value, self is not required
        if (self_obj.val() == '' && target_obj.val() != '') {
            target_obj.attr('required', '');
            self_obj.removeAttr('required');
        } else if (self_obj.val() != '' && target_obj.val() == '') {
            // if self has value but target has no value,
            // self is required, target is not required
            self_obj.attr('required', '');
            target_obj.removeAttr('required');
        } else {
            self_obj.attr('required', '');
            target_obj.attr('required', '');
        }
    } catch(err) {
        console.log(err);
    }
}