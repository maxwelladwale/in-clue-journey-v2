{
    'name': 'iN-Clue Journey Event Survey',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Link events with surveys for the iN-Clue Journey experience',
    'description': """
        This module enables linking of events to surveys.
        It tracks participant sessions (kickoff & follow-up) to allow later
        analysis and automated follow-ups.
    """,
    'author': 'Your Name or Company',
    'depends': ['base', 'event', 'survey', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/res_partner_view.xml',
        'views/event_form.xml',
        'views/participation_tracking.xml',
        'data/email_templates.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
}