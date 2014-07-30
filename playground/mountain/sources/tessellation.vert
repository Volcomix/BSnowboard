#version 410 core

layout(location=0) in vec4 vertex;

out gl_PerVertex {
    vec4 gl_Position;
};

void main()
{
	gl_Position = vertex;
}


