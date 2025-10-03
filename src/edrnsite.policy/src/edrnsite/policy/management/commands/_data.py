# encoding: utf-8

'''🧬 EDRN Site Policy: initial data.'''

from wagtail.rich_text import RichText
import importlib.resources, os.path, csv, codecs

# The grant numbers come from the file `data/grant-numbers.txt`
GRANT_NUMBERS = importlib.resources.read_text(__name__, 'data/grant-numbers.txt').strip().split('\n')

# Boilerplate things like legal disclaimers or other notices
_bp = 'data/boilerplate'
BOILERPLATES = [
    (os.path.splitext(i)[0], importlib.resources.read_text(__name__, _bp + '/' + i).strip())
for i in importlib.resources.resource_listdir(__name__, _bp)]  # noqa: E122

# Laboratory certifications
CERTIFICATIONS = (
    (
        'http://www.cms.gov/Regulations-and-Guidance/Legislation/CLIA/index.html',
        'CLIA',
        'Centers for Medicare & Medicaid Services Clinical Laboratory Improvement Amendments'
    ),
    (
        'http://www.fda.gov/regulatoryinformation/guidances/ucm125335.htm',
        'FDA',
        'Food & Drug Administration Certification'
    ),
)

# Rich text for each section description
SECTION_DESCRIPTIONS = {
    'about': {
        'mission': RichText('<p>Organizational and operational design, components, collaborative groups, and interagency agreements.</p>'),
        'fda': RichText('<p>Information about the tests and devices that are approved for use.</p>'),
        'clia': RichText('<p>Information about the EDRN-developed biomarker tests availalbe in Clinical Laboratory Improvement Amendments-approved laboratories.</p>'),
        'stupid': RichText('<p>About the systems and standards created to validate biomarkers.</p>'),
        'info': RichText('<p>The infrastructure and tools that connect the EDRN research institutions together into a virtual knowledge system.</p>'),
        'history': RichText('<p>A brief history of how the need for EDRN was identified and how it came into creation.</p>'),
        'book': RichText('<p>Documents relevant to the Early Detection Research Network.</p>'),
        'sites': RichText('<p>The institutions and investigators that comprise the network.</p>'),
    },
    'work': {
        'assoc': RichText('<p>Opportunities for investigators not currently affiliated with EDRN to join the EDRN community.</p>'),
        'vsp': RichText('<p>Pre-proposal and proposal guidelines for validation studies within EDRN.</p>'),
        'funding': RichText('<p>Future announcements of funding opportunities.</p>'),
        'pubpriv': RichText('<p>Guidelines and existing partnerships with public and private entities.</p>'),
        'tool': RichText('<p>A DMCC tool to find collaborators within EDRN with a keyword search.</p>'),
        'advocacy': RichText('<p>Information for cancer patients and their advocates.</p>'),
        'mous': RichText('<p>Agreements between the National Cancer Institute and other agencies.</p>'),
        'mf': RichText('<p>Find EDRN members by type, PI, or institute.</p>')
    },
    'news': {
        'newsletter': RichText('<p>The newsletter of the Early Detection Research Network.</p>'),
        'reports': RichText('<p>Proceedings, presentations, and other material from past meetings.</p>'),
        'blog': RichText('<p>A research blog from the NCI Division of Cancer Prevention.</p>'),
        'webinars': RichText('<p>Web-based seminars.</p>'),
        'registration': RichText('<p>Upcoming meetings.</p>'),
    },
}

# The utterly stupid title for the five phase approach heading, which is too hecking long
STUPID_TITLE = 'Five-Phase Approach and Prospective specimen collection, Retrospective Blinded Evaluation Study Design'

# Body text for a web page describing the Prevention Science Blog
PREVENTION_SCIENCE_BLOG = RichText('''
<p>
The <a href="https://prevention.cancer.gov/news-and-events/blog">NCI Prevention Science Blog</a> is a
periodically updated weblog from the NCI Division of Cancer Prevention describing the latest research into
the science of the prevention of cancer.
</p>
<p>
<b>Please be sure to <a href="https://prevention.cancer.gov/news-and-events/blog">check it out</a>!</b>
</p>
''')

# For the meeting reports page
MEETING_REPORTS_TEMPLATE = '''
<p>Steering Committee Meetings</p>
<ul>
<li><a id="{sc38}" linktype="page">38th</a></li>
<li><a id="{sc37}" linktype="page">37th</a></li>
<li><a id="{sc36}" linktype="page">36th</a></li>
<li><a id="{sc35}" linktype="page">35th</a></li>
</ul>
<p>Scientific Workshops</p>
<ul>
<li><a id="{scimtg}" linktype="page">12th</a></li>
</ul>
'''

# Text for the find-a-sponsor-tool interstitial page
FIND_A_SPONSOR_TOOL_RICH_TEXT = RichText('''
<p>
The <a href="http://www.compass.fhcrc.org/edrnnci/bin/search/search.asp?t=search&amp;cer=&amp;rd_deny=z0&amp;f32=96p&amp;etc">Find
a Sponsor Tool</a> is a web resource maintained by EDRN's
<a href="https://www.fredhutch.org/en/research/divisions/public-health-sciences-division/research/biostatistics/comprehensive-center-for-advancement-scientific-strategies-compass.html">Data
Management and Coordinating Center</a> that helps you find a collaborator and/or sponsor.
</p>
<p>
<b>Please be sure to <a href="http://www.compass.fhcrc.org/edrnnci/bin/search/search.asp?t=search&amp;cer=&amp;rd_deny=z0&amp;f32=96p&amp;etc">check it out</a>!</b>
</p>
''')

MEMBER_FINDER_TEMPLATE = '''
<p>
The <a href="{url}">member finder</a> lets you see the people that comprise EDRN. It includes pick-lists for
principal investigator and institution and checkboxes for the types of EDRN members.
</p>
<p><a href="{url}">Give it a try</a>.</p>
'''

# Template for the alt text for the home page image carousel; must have a {} to fill in
CAROUSEL_ALT_TEMPLATE = 'Emblematic image of the Early Detection Research Network featuring a {} background'

# Carousel heading & captions
CAROUSEL_CAPTIONS = (
    ('The Early Detection Research Network', 'Stimulating collaborative discovery, development, and validation of biomarkers for cancer risk and early detection.'),
    ('Biomarkers', 'The key to early detection.'),
    ('Over 1600 Biomarkers', "More biomarker research means earlier detection—which results in better patient outcomes.")
)

# URL to the off-site "find a sponsor" tool
SPONSOR_TOOL_URL = 'http://www.compass.fhcrc.org/edrnnci/bin/search/search.asp?t=search&cer=&rd_deny=z0&f32=96p&etc'

# URL to the NCI science blog
BLOG_URL = 'https://prevention.cancer.gov/news-and-events/blog'

# Images, captions, and more for the data-and-resources SectionPage; the tuple members are:
#     identifier, title, description, image alt text
# where the identifier identifies which page underneath data-and-resources it is, plus if prefixed
# by `dr-` and suffixed by `.jpg` tells what image to use.
DATA_AND_RESOURCES = (
    ('biomarkers', 'Biomarker Database', 'A searchable catalog of biomarkers researched by the EDRN community.', 'DNA and other material representative of biomarkers'),
    ('specimens', 'Specimen Reference Sets and Research Tools', 'Reference sets, statistical support tools, and more.', 'An image of sample tubes being filled with a dispenser'),
    ('protocols', 'Protocols', 'A list of the EDRN protocols that have been captured and curated. Additional information will be added as it is available. Contact information is provided as part of the detail for each protocol.', 'A physician with a stethoscope and protective gloves'),
    ('informatics', 'Informatics', 'Tools for comprehensive information including an integrated knowledge environment for capturing, managing, integrating, and sharing results.', 'An abstract background representing data with computer monitors in the foreground'),
    ('data', 'Data', 'A searchable collection of datasets produced by the EDRN community.', 'A physician in front of a modern computing device'),
    ('publications', 'Publications', 'Published research from EDRN investigators, searchable by author, journal, and more.', 'An photograph of upright books, but not their spines—their opposite page sides instead.'),
    ('cde', 'CDEs', 'Common Data Elements.', "A photograph from the Cancer Visuals Online project of a librarian at the National Library of Medicine using a computer to access the Physicians Data Query (PDQ), used as an emblematic image for EDRN's common data elements (CDEs)."),
    ('sop', 'SOPs', 'Standard Operating Procedures.', "A photograph from the Cancer Visuals Online project of blood specimen vials serving as a visual representation of the end product of standard operating procedures."),
    ('stats', 'Statistical Resources', 'Numerical models, statistical methods, and other mathematical resources developed by the Data Management and Coordinating Center.', "A photograph from the Cancer Visuals Online project of person compiling health statistics, serving as a visual representation of statistical resources.")
)

INFORMATICS_BODY = '''<p>
    See also the <a id="{informatics_faq}" linktype="page">Informatics FAQ: frequently asked questions—with answers</a>.
</p>

<h2>Tools</h2>

<dl>
    <dt>EDRN Knowledge System</dt>
    <dd>Both public and secure access to the programmatic and scientific results of EDRN research. <small>Open to the public. EDRN login gains greater access.</small></dd>

    <dt><a href="https://edrn-labcas.jpl.nasa.gov/labcas-ui/m/index.html">LabCAS</a></dt>
    <dd>An infrastructure for investigators in EDRN to securely capture, process, and dissemination data to other investigators. <small>EDRN login required.</small>
    </dd>

    <dt><a href="https://www.compass.fhcrc.org/vs/login.asp?pt=&amp;m=&amp;n=&amp;o=&amp;p=&amp;q=&amp;p1=71ab3c03">VSIMS</a></dt>
    <dd>A tool, developed by <a href="http://www.fhcrc.org/">Fred Hutchinson Cancer Research Center</a>, used to support EDRN validation studies. <small>EDRN login required.</small>
    </dd>

    <dt><a href="https://www.compass.fhcrc.org/edrnpub/bin/protocol/searchESIS.asp?t=QuickSearch">eSIS</a>
    </dt>
    <dd>A database of EDRN protocols. <small>EDRN login required.</small></dd>

    <dt><a href="https://www.compass.fhcrc.org/enterEDRN">Secure Site</a></dt>
    <dd>An internal EDRN site hosted by the EDRN DMCC for sharing policies and other information. <small>EDRN login required.</small></dd>

    <dt><a href="https://oncomx.org/">OncoMX</a></dt>
    <dd>An integrated cancer mutation and expression resource for exploring cancer biomarkers alongside related experimental data and functional information. Open to the public.</dd>
</dl>

<h2>Data</h2>

<ul>
    <li><a id="{biomarkers}" linktype="page">Biomarker Data</a></li>
    <li><a id="{protocols}" linktype="page">Protocols</a></li>
    <li><a id="{publications}" linktype="page">Publications</a></li>
    <li><a id="{data}" linktype="page">Science Data</a></li>
</ul>

<h2>Standards</h2>
    <ul>
        <li><a id="{cdes}" linktype="document">EDRN Common Data Elements</a> [XLSX file, 227KB].
            A set of EDRN CDEs developed by the program to support data annotation and sharing.</li>
        <li><a href="https://osp.od.nih.gov/wp-content/uploads/NIH_Best_Practices_for_Controlled-Access_Data_Subject_to_the_NIH_GDS_Policy.pdf">NIH Security Best Practices for Controlled-Access Data Subject to the NIH Genomic Data Sharing (GDS) Policy</a></li>
</ul>



<h2>Leadership</h2>

<p>EDRN informatics leadership is provided by the <a href="https://www.jpl.nasa.gov/">Jet Propulsion Laboratory</a>'s EDRN Informatics Center and the <a href="https://www.fredhutch.org/en/research/divisions/public-health-sciences-division/research/biostatistics/comprehensive-center-for-advancement-scientific-strategies-compass.html">Fred Hutchinson EDRN Data Management and Coordinating Center (DMCC)</a>.</p>
'''


def _static_sites():
    static_sites = []
    for fn, heading, intro in (
        ('cvc', 'Clinical Validation Centers (CVCs)', 'The Centers conduct clinical and epidemiological research regarding the clinical application of biomarkers.'),
        ('dmcc', 'Data Management and Coordinating Center', 'The Center is responsible for coordinating the EDRN research activities, providing logistic support, and conducting statistical and computational research for data analysis, analyzing data for validation. The data center will develop a common database for Network research.'),
        ('bcc', 'Biomarker Characterization Center (BCCs)', 'Centers that characterize biomarkers.'),
        ('bdl', 'Biomarker Developmental Laboratories (BDLs)', 'Laboratories that develop biomarkers.'),
        ('brl', 'Biomarker Reference Laboratories (BRLs)', 'Laboratories that reference biomarkers.')
    ):
        try:
            static_sites.append(f'<h2>{heading}</h2>')
            static_sites.append(f'<p>{intro}</h2>')
            static_sites.append('<table class="table"><thead><tr><th>Group</th><th>Site ID</th><th>Name</th><th>Institution</th><th>PI Type</th><th>Member Type</th><th>Organ</th></tr></thead><tbody>')

            reader = codecs.getreader('utf-8')
            source = reader(importlib.resources.resource_stream(__name__, f'data/sites/{fn}.csv'))
            reader = csv.reader(source)

            for row in reader:
                static_sites.append('<tr>')
                for col in row:
                    static_sites.append(f'<td>{col}</td>')
                static_sites.append('</tr>')

            static_sites.append('</tbody></table>')
        finally:
            source.close()
    return ''.join(static_sites)


STATIC_SITES = RichText(_static_sites())


def main():
    print(STATIC_SITES)


if __name__ == '__main__':
    main()
