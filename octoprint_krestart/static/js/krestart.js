$(function() {
    function KrestartControlViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];


        self.togglePrinter = function() {
            showConfirmationDialog({
                message: "Do you want to toggle the printer?",
                onproceed: function() {
                    $.ajax({
                        url: API_BASEURL + "plugin/krestart",
                        type: "POST",
                        dataType: "json",
                        data: JSON.stringify({
                            command: "togglePrinter"
                        }),
                        contentType: "application/json; charset=UTF-8"
                    })
                }
            });
        };

        self.toggleLight = function() {
            $.ajax({
                url: API_BASEURL + "plugin/krestart",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "toggleLight"
                }),
                contentType: "application/json; charset=UTF-8"
            })
        };
    }

    ADDITIONAL_VIEWMODELS.push([
        KrestartControlViewModel,
        ["loginStateViewModel"],
        ["#navbar_plugin_krestart"]
    ]);
});
