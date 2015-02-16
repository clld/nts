<%inherit file="../home_comp.mako"/>
<%namespace name="util" file="../util.mako"/>

<%def name="sidebar()">
##<div id="wals_search">
##<script>
##(function() {
##var cx = '012093784907070887713:a7i_0y3rwgs';
##var gcse = document.createElement('script');
##gcse.type = 'text/javascript';
##gcse.async = true;
##gcse.src = (document.location.protocol == 'https:' ? 'https:' : 'http:') +
##'//www.google.com/cse/cse.js?cx=' + cx;
##var s = document.getElementsByTagName('script')[0];
##s.parentNode.insertBefore(gcse, s);
##})();
##</script>
##<gcse:search></gcse:search>
##</div>
</%def>

<h2>Welcome to NTS Online</h2>

<p class="lead">
The Nijmegen Typological Survey (NTS) is a large database of grammatical properties of languages gathered from descriptive
materials (such as reference grammars) by a team directed by Stephen C. Levinson. The original questionnaire was
designed by Ger Reesink and Michael Dunn, subsequent extensions and clarifications were done by Hedvig Skirg&aring;rd,
Suzanne van der Meer and Harald Hammarstr&ouml;m.
</p>

<p>
<table class="table table-condensed table-nonfluid">
    <thead>
    <tr>
        <th>Statistics</th>
        <th></th>
    </tr>
    </thead>
    <tbody>
    <tr><td>Languages</td><td>${stats['language']}</td></tr>
    <tr><td>Features</td><td>${stats['parameter']}</td></tr>
    <tr><td>Datapoints</td><td>${stats['value']}</td></tr>
    </tbody>
</table>
</p>

<p>
NTS Online is a publication of the
${h.external_link('http://www.mpi.nl/lnc/TODO', label='Language and Cognition Group (LnC)')} at the Max Planck Institute for Psycholinguistics, Nijmegen.
</p>

<h3>How to use NTS Online</h3>
<p>
Using NTS Online requires a browser with Javascript enabled.
</p>
<p>
You find the features or languages of NTS through the items "Features" and "Languages"
in the navigation bar.
</p>



<h3>How to cite NTS Online</h3>
<p>
TODO
</p>

<h3>WiP Documents</h3>
<p>
Links to some NTS-related work-in-progress documents:
<ulist>
<ul><a href="https://docs.google.com/document/d/1UlqtSUQVk6MopqE0WSE_6fgCqbtyX_lCc312KdLU6s8/edit?usp=sharing">Meeting notes</a></ul>

<ul><a href="https://docs.google.com/document/d/1UlqtSUQVk6MopqE0WSE_6fgCqbtyX_lCc312KdLU6s8/edit?usp=sharing">Collaborative feature sheet</a></ul>

<ul><a href="https://docs.google.com/spreadsheets/d/1siyF5x9tufISU9E42uj5VWzokLnVvdzYlQpHrhHs-CI/edit#gid=0">NTS languages covered and contact details</a></ul>
</ulist>
</p>

<h3>Terms of use</h3>
<p>
The content of this web site is published under a Creative Commons Licence.
We invite the community of users to think about further applications for the available data
and look forward to your comments, feedback and questions.
</p>