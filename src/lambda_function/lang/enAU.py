from lambda_function.lang.language import Key
'''
To add another language create a file using the code below, without the hyphen (-).
Use the same keys in the LANGUAGE dictionary and update the spoken values.
    ar-SA: Arabic (SA)
    de-DE: German (DE)
    en-AU: English (AU)
    en-CA: English (CA)
    en-GB: English (UK)
    en-IN: English (IN)
    en-US: English (US)
    es-ES: Spanish (ES)
    es-MX: Spanish (MX)
    es-US: Spanish (US)
    fr-CA: French (CA)
    fr-FR: French (FR)
    hi-IN: Hindi (IN)
    it-IT: Italian (IT)
    ja-JP: Japanese (JP)
    pt-BR: Portuguese (BR)
'''

LANGUAGE = {
    Key.CardTitle: 'Alexa Chromecast Controller',
    Key.Help: '''
    Welcome to the Alexa Chromecast controller. This skill allows you to control your Chromecasts in different rooms.
    An Alexa Device can be configured to control a Chromecast in a particular room.
    Then you can say something like: Alexa, ask Chromecast to play, or: Alexa, ask Chromecast to pause.
    Or you can control a specific room, by saying something like: Alexa, ask Chromecast to play in the media room.
    ''',
    Key.Ok: 'Ok',
    Key.Goodbye: 'Goodbye!',
    Key.ErrorGeneral: 'Sorry, I had trouble doing what you asked. Please try again.',

    # Set the room
    Key.SetTheRoom: 'I need to set the room of the Chromecast that this Alexa device will control. ' +
                  'Please say something like: set room to media room.',
    Key.ShortSetTheRoom: 'Please set the Chromecast\'s room, by saying something like: set room to media room.',
    Key.ControlRoom: 'Ok, this Alexa device will control the Chromecast in the {room}.',

    # Set Volume
    Key.SetVolume: 'Ok, changing volume to {volume}.',
    Key.IncreaseVolume: 'Ok, increasing volume.',
    Key.DecreaseVolume: 'Ok, reducing volume.',

    # Subtitles
    Key.SubtitlesOff: 'Ok, turning subtitles off',
    Key.SubtitlesOn: 'Ok, turning subtitles on',

    # SNS Publish
    Key.LogErrorSnsPublish: 'Sending command to the Chromecast failed',
    Key.ErrorSnsPublish: 'Sorry, there was an error sending the command to the Chromecast. ',

    # Switch Audio
    Key.SwitchAudio: 'Ok, changing the audio stream.',

    # QualityIntent
    Key.ChangeQuality: 'Ok, changing media quality to {quality}.',
    Key.IncreaseQuality: 'Ok, increasing media quality.',
    Key.DecreaseQuality: 'Ok, reducing media quality.',
    Key.ErrorChangeQuality: 'Sorry I was unable to change the quality. Please try again.',

    Key.ErrorEpisodeParams: 'I can\'t do that. You need to specify a season or an episode.',
    Key.ErrorSetVolumeRange: 'Sorry, you can only set the volume between 0 and 10. Please try again.',

    # Play Media Types
    Key.Playing: 'Playing',
    Key.Finding: 'Finding',
    Key.Shuffling: 'Shuffling',

    Key.InRoom: 'in {room}',
    Key.OnApp: 'on {app}',

    # Play music
    Key.PlayTitle: '{play} {title}',
    Key.PlaySongsByArtist: '{play} songs by {artist}',
    Key.PlaySong: '{play} song {title}',
    Key.PlaySongsByAlbum: '{play} album {album}',

    # Play photos
    Key.PlayPhotosByDate: '{play} photos from {month} {year}',
    Key.PlayPhotosByEvent: '{play} photos from {title} {year}',
    Key.PlayPhotosByTitle: '{play} photos from {title}',
    Key.PlayPhotosByYear: '{play} photos from {year}',

    # Play media
    Key.PlayPlaylist: '{play} playlist {title}',
    Key.PlayMovie: '{play} movie {title}',
    Key.PlayShow: '{play} the show {show}',
    Key.PlayEpisode: '{play} episode {title} of {show}',
    Key.PlayEpisodeNumber: '{play} episode {episode} of season {season} of {show}',
    Key.PlaySeason: '{play} season {season} of {show}',

    # Speech to pronounce definitions like "1080p"
    Key.Speak1080p: 'ten eighty pea',
    Key.Speak720p: 'seven twenty pea',
    Key.Speak480p: 'four eighty pea',

    # List of months based on Amazon Month slot type
    Key.ListMonths: ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
                     'september', 'october', 'november', 'december']

}
