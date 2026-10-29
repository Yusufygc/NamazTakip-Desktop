import QtQuick
import QtQuick.Shapes
import "../theme"

// Merkezi ikon: `name` Icons.paths içindeki anahtardır.
Item {
    id: root

    property string name: ""
    property color color: Theme.text
    property real size: 24
    property real strokeWidth: 2

    width: size
    height: size
    Accessible.ignored: true

    Shape {
        width: 24
        height: 24
        scale: root.size / 24
        transformOrigin: Item.TopLeft
        preferredRendererType: Shape.CurveRenderer

        ShapePath {
            strokeColor: root.color
            strokeWidth: root.strokeWidth
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin

            PathSvg {
                path: Icons.paths[root.name] !== undefined ? Icons.paths[root.name] : ""
            }
        }
    }
}
