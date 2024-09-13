# AUTO GENERATED FILE - DO NOT EDIT

#' @export
dashPannellum <- function(id=NULL, autoLoad=NULL, compass=NULL, currentScene=NULL, customControls=NULL, height=NULL, multiRes=NULL, northOffset=NULL, pitch=NULL, showCenterDot=NULL, tour=NULL, video=NULL, width=NULL, yaw=NULL) {
    
    props <- list(id=id, autoLoad=autoLoad, compass=compass, currentScene=currentScene, customControls=customControls, height=height, multiRes=multiRes, northOffset=northOffset, pitch=pitch, showCenterDot=showCenterDot, tour=tour, video=video, width=width, yaw=yaw)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'DashPannellum',
        namespace = 'dash_pannellum',
        propNames = c('id', 'autoLoad', 'compass', 'currentScene', 'customControls', 'height', 'multiRes', 'northOffset', 'pitch', 'showCenterDot', 'tour', 'video', 'width', 'yaw'),
        package = 'dashPannellum'
        )

    structure(component, class = c('dash_component', 'list'))
}
