function launchcontrol

% make a GUI that resembles the Novation LaunchControl XL

close all
h = figure;
set(h, 'MenuBar', 'none')
set(h, 'Name', 'LaunchControl XL')
pos = get(h, 'Position');
pos(3) = 550;
pos(4) = 380;
set(h, 'Position', pos);

uicontrol('tag', '1_control', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_focus',   'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '1_slide',   'callback', @callback, 'style', 'slider',     'string', '');
uicontrol('tag', '1_pan',     'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '1_sendB',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '1_sendA',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});

uicontrol('tag', '2_control', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_focus',   'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '2_slide',   'callback', @callback, 'style', 'slider',     'string', '');
uicontrol('tag', '2_pan',     'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '2_sendB',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '2_sendA',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});

uicontrol('tag', '3_control', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_focus',   'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '3_slide',   'callback', @callback, 'style', 'slider',     'string', '');
uicontrol('tag', '3_pan',     'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '3_sendB',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '3_sendA',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});

uicontrol('tag', '4_control', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_focus',   'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '4_slide',   'callback', @callback, 'style', 'slider',     'string', '');
uicontrol('tag', '4_pan',     'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '4_sendB',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '4_sendA',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});

uicontrol('tag', '5_control', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_focus',   'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '5_slide',   'callback', @callback, 'style', 'slider',     'string', '');
uicontrol('tag', '5_pan',     'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '5_sendB',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '5_sendA',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});

uicontrol('tag', '6_control', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_focus',   'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '6_slide',   'callback', @callback, 'style', 'slider',     'string', '');
uicontrol('tag', '6_pan',     'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '6_sendB',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '6_sendA',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});

uicontrol('tag', '7_control', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_focus',   'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '7_slide',   'callback', @callback, 'style', 'slider',     'string', '');
uicontrol('tag', '7_pan',     'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '7_sendB',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '7_sendA',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});

uicontrol('tag', '8_control', 'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '8_focus',   'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '8_slide',   'callback', @callback, 'style', 'slider',     'string', '');
uicontrol('tag', '8_pan',     'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '8_sendB',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});
uicontrol('tag', '8_sendA',   'callback', @callback, 'style', 'popupmenu',  'string', {'0', '1', '2', '3', '4', '5' ,'6', '7', '8', '9'});

uicontrol('tag', '0_record',        'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_solo',          'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_mute',          'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_device',        'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_track_selectL', 'callback', @callback, 'style', 'pushbutton', 'string', '<');
uicontrol('tag', '0_track_selectR', 'callback', @callback, 'style', 'pushbutton', 'string', '>');
uicontrol('tag', '0_send_selectL',  'callback', @callback, 'style', 'pushbutton', 'string', '<');
uicontrol('tag', '0_send_selectR',  'callback', @callback, 'style', 'pushbutton', 'string', '>');
uicontrol('tag', '0_user',          'callback', @callback, 'style', 'pushbutton', 'string', '');
uicontrol('tag', '0_factory',       'callback', @callback, 'style', 'pushbutton', 'string', '');

ft_uilayout(h, 'tag', 'control$', 'position', [0 0 050 030]);
ft_uilayout(h, 'tag', 'focus$',   'position', [0 0 050 030]);
ft_uilayout(h, 'tag', 'slide$',   'position', [0 0 060 160]);
ft_uilayout(h, 'tag', 'pan$',     'position', [0 0 060 020]);
ft_uilayout(h, 'tag', 'sendA$',   'position', [0 0 060 020]);
ft_uilayout(h, 'tag', 'sendB$',   'position', [0 0 060 020]);

ft_uilayout(h, 'tag', '^1_', 'hpos', 040);
ft_uilayout(h, 'tag', '^2_', 'hpos', 090);
ft_uilayout(h, 'tag', '^3_', 'hpos', 140);
ft_uilayout(h, 'tag', '^4_', 'hpos', 190);
ft_uilayout(h, 'tag', '^5_', 'hpos', 240);
ft_uilayout(h, 'tag', '^6_', 'hpos', 290);
ft_uilayout(h, 'tag', '^7_', 'hpos', 340);
ft_uilayout(h, 'tag', '^8_', 'hpos', 390);

ft_uilayout(h, 'tag', 'control$', 'vpos', 020);
ft_uilayout(h, 'tag', 'focus$',   'vpos', 050);
ft_uilayout(h, 'tag', 'slide$',   'vpos', 090);
ft_uilayout(h, 'tag', 'pan$',     'vpos', 260);
ft_uilayout(h, 'tag', 'sendA$',   'vpos', 290);
ft_uilayout(h, 'tag', 'sendB$',   'vpos', 320);

ft_uilayout(h, 'tag', 'slide$',   'hshift', -25);

ft_uilayout(h, 'tag', '^0_', 'position', [0 0 20 20]);
ft_uilayout(h, 'tag', '^0_', 'hpos', 480);
ft_uilayout(h, 'tag', '0_record',        'vpos', 105);
ft_uilayout(h, 'tag', '0_solo',          'vpos', 140);
ft_uilayout(h, 'tag', '0_mute',          'vpos', 175);
ft_uilayout(h, 'tag', '0_device',        'vpos', 210);
ft_uilayout(h, 'tag', '0_track_selectL', 'vpos', 260, 'hshift', -15);
ft_uilayout(h, 'tag', '0_track_selectR', 'vpos', 260, 'hshift',  15);
ft_uilayout(h, 'tag', '0_send_selectL',  'vpos', 290, 'hshift', -15);
ft_uilayout(h, 'tag', '0_send_selectR',  'vpos', 290, 'hshift',  15);
ft_uilayout(h, 'tag', '0_user',          'vpos', 320, 'hshift', -15);
ft_uilayout(h, 'tag', '0_factory',       'vpos', 320, 'hshift',  15);


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SUBFUNCTION
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function callback(h, event)
disp(get(h, 'tag'))
