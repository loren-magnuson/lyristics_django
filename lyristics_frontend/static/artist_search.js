/**
 * Created by magno on 1/25/17.
 */
$(function() {
  $("#main_search_box").autocomplete({
    source: "autocomplete",
    minLength: 1,
    select: function(event, ui) {
      window.location.href = 'artist' + '?artist_id=' + ui.item.id;
    },
    open: function(event, ui) {
        $(".ui-autocomplete").css("z-index", 1000);
    }
  });
});
// $(function() {
//   $("#nav_search_box").autocomplete({
//     source: "/autocomplete",
//     minLength: 1,
//     select: function(event, ui) {
//       window.location.href = 'artist' + "?artist_id=" + ui.item.id;
//     },
//     open: function(event, ui) {
//         $(".ui-autocomplete").css("z-index", 1000);
//     }
//   });
// });

$(function() {
    $('#main_search_form').on('submit', function(e) { //use on if jQuery 1.7+
        e.preventDefault();  //prevent form from submitting

        var query = $("#main_search_box").val();

        data = $.getJSON('/search/', {term: query}, function(data, jqXHR) {
          //  total_hits = data.hits.total;
         //   hits = data.hits.hits;
            show_search_results(data)})
        });
});


function show_search_results(data) {
    var results_container = $('#results-container');
    var search_term = $("#search-term");
    var results_count = $('#results-count');
    var total_hits = data.count;
    var search_results = JSON.parse(data.mongo_items);
    var query = data.query;

    if ($(results_container).hasClass("hidden")) {
        results_container.hide();
        results_container.removeClass("hidden");
        $(search_term).text(query);
        $(results_count).text(" " + total_hits + " ");
    }
    else {
        $(search_term).fadeTo(duration=800, opacity=0, complete=function() {
            $(search_term).text(query);
            $(search_term).fadeTo(opacity=1, duration=800);
            console.log(query)
        });
        $(results_count).fadeTo(duration=800, opacity=0,complete=function() {
            $(results_count).text(" " + total_hits + " ");
            $(results_count).fadeTo(opacity=1, duration=800);
        });
    }
    //
    var result_section = $("#results");
    var are_results_empty = $(".search-result");
    if (are_results_empty != null) {
        $(result_section).empty();
    }
    console.log(search_results);
    $.each(search_results, function (i, item) {
        // $.each(item.fields, function (key, val) {
        var fields = item.fields;
        console.log(fields);

            var result_template = $('.search_result_template').clone();
            var img_thumbnail = $(result_template).find("a.thumbnail > img");

            var result_header = $(result_template).find("h3 > a");
            $(result_header).text(fields.artist_name);
          
            if (fields.artist_images[0]) {
                 $(img_thumbnail).attr('src', "/static/images/" + fields.artist_images[0].path);
            }

            // $(img_link).attr('href', "/artist?artist_id=" + item._id);
            var date_scraped = $(result_template).find(".meta-search > li > span.date-scraped");
            var time_scraped = $(result_template).find(".meta-search > li > span.time-scraped");
            var property_status = $(result_template).find(".meta-search > li > span.property-status");
          //  $(property_status).text(fields.property_status);
           // var last_checked_date = fields.last_checked.split("T")[0];
           // var last_checked_time = fields.last_checked.split("T")[1].split("Z")[0];
            //$(date_scraped).text(last_checked_date);
           // $(time_scraped).text(last_checked_time);

            var result_excerpt = $(result_template).find(".excerpt > p");
            if (fields.property_status == "null") {
                $(result_excerpt).append("This property's status is <b>Unknown</b>. ");
            }

            $(result_section).append(result_template);
            $(result_template).hide();
            $(result_template).addClass("search-result");
            $(result_template).removeClass("hidden").removeClass('search_result_template');
        });
    $('#articles').slideUp(duration = 800, complete=function () {
        results_container.fadeIn(duration = 800, complete=function () {
            $(".search-result").each(function (i, item) {
                $(item).fadeIn(duration = 1600);
            });
        });
    });
}

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});
